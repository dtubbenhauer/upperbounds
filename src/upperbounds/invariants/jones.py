"""Jones polynomial computations from planar diagrams."""

from __future__ import annotations

from fractions import Fraction
from typing import TypeAlias


Polynomial: TypeAlias = dict[int, int]


def poly_add(left: Polynomial, right: Polynomial) -> Polynomial:
    """Add two sparse Laurent polynomials.

    Args:
        left: Left polynomial keyed by exponent.
        right: Right polynomial keyed by exponent.

    Returns:
        The sum as a sparse polynomial.
    """
    result = dict(left)
    for exponent, coefficient in right.items():
        result[exponent] = result.get(exponent, 0) + coefficient
        if result[exponent] == 0:
            del result[exponent]
    return result


def poly_mul(left: Polynomial, right: Polynomial) -> Polynomial:
    """Multiply two sparse Laurent polynomials.

    Args:
        left: Left polynomial keyed by exponent.
        right: Right polynomial keyed by exponent.

    Returns:
        The product as a sparse polynomial.
    """
    result: Polynomial = {}
    for left_exp, left_coeff in left.items():
        for right_exp, right_coeff in right.items():
            exponent = left_exp + right_exp
            result[exponent] = (
                result.get(exponent, 0) + left_coeff * right_coeff
            )
    return {
        exponent: coefficient
        for exponent, coefficient in result.items()
        if coefficient != 0
    }


def poly_monom(exp: int, coeff: int = 1) -> Polynomial:
    """Return a single-term sparse polynomial."""
    return {int(exp): int(coeff)}


def poly_scale(poly: Polynomial, scalar: int) -> Polynomial:
    """Scale a sparse Laurent polynomial by an integer."""
    return {
        exponent: coefficient * scalar
        for exponent, coefficient in poly.items()
        if coefficient * scalar != 0
    }


class DSU:
    """Disjoint-set union used by the Kauffman bracket state sum."""

    def __init__(self) -> None:
        """Initialize an empty disjoint-set structure."""
        self.parents: dict[int, int] = {}

    def find(self, item: int) -> int:
        """Return the representative for an item."""
        if item not in self.parents:
            self.parents[item] = item
        while self.parents[item] != item:
            self.parents[item] = self.parents[self.parents[item]]
            item = self.parents[item]
        return item

    def union(self, left: int, right: int) -> None:
        """Union the sets containing two items."""
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parents[right_root] = left_root

    def n_components(self) -> int:
        """Return the current number of connected components."""
        return len({self.find(item) for item in self.parents})


def bracket_from_pd(pd: list[tuple[int, int, int, int]]) -> Polynomial:
    """Compute the Kauffman bracket from a planar diagram.

    Args:
        pd: Planar diagram crossing quadruples.

    Returns:
        Sparse polynomial in the bracket variable.
    """
    crossing_count = len(pd)
    delta = poly_add(
        poly_scale(poly_monom(2), -1),
        poly_scale(poly_monom(-2), -1),
    )

    labels = set()
    for left, top, right, bottom in pd:
        labels.update([left, top, right, bottom])

    total: Polynomial = {}
    for mask in range(1 << crossing_count):
        dsu = DSU()
        for label in labels:
            dsu.find(label)

        a_count = 0
        b_count = 0
        for index, (left, top, right, bottom) in enumerate(pd):
            if ((mask >> index) & 1) == 0:
                a_count += 1
                dsu.union(left, top)
                dsu.union(right, bottom)
            else:
                b_count += 1
                dsu.union(top, right)
                dsu.union(bottom, left)

        loops = dsu.n_components()
        monomial = poly_monom(a_count - b_count, 1)

        factor = {0: 1}
        for _ in range(loops - 1):
            factor = poly_mul(factor, delta)

        total = poly_add(total, poly_mul(monomial, factor))
    return total


def crossing_sign_pd(quad: tuple[int, int, int, int]) -> int:
    """Return the crossing sign convention used by existing notebooks."""
    left, top, right, bottom = quad
    return 1 if (left < right) == (top < bottom) else -1


def jones_string_from_pd(
    pd_list: list[list[int]],
) -> tuple[str | None, str | None]:
    """Compute a Jones polynomial string from a planar diagram.

    Args:
        pd_list: Planar diagram crossing quadruples.

    Returns:
        `(polynomial_string, error)`, matching existing notebook behavior.
    """
    if not pd_list:
        return None, "Empty PD"
    pd_quads = [tuple(map(int, quad)) for quad in pd_list]
    try:
        bracket = bracket_from_pd(pd_quads)
        writhe = sum(crossing_sign_pd(quad) for quad in pd_quads)
        sign = -1 if ((-3 * writhe) % 2) else 1
        normalization = poly_scale(poly_monom(-3 * writhe, 1), sign)
        normalized = poly_mul(normalization, bracket)

        jones_terms: dict[Fraction, int] = {}
        for exponent_a, coefficient in normalized.items():
            exponent_t = Fraction(-exponent_a, 4)
            jones_terms[exponent_t] = (
                jones_terms.get(exponent_t, 0) + coefficient
            )
        jones_terms = {
            exponent: coefficient
            for exponent, coefficient in jones_terms.items()
            if coefficient != 0
        }

        terms = []
        for exponent in sorted(jones_terms.keys(), reverse=True):
            if exponent.denominator != 1:
                raise ValueError(
                    f"Non-integral exponent encountered: {exponent}"
                )
            coefficient = jones_terms[exponent]
            power = exponent.numerator
            if power == 0:
                monomial = ""
            elif power == 1:
                monomial = "t"
            else:
                monomial = f"t^{power}"

            if monomial == "":
                term = f"{coefficient}"
            elif coefficient == 1:
                term = monomial
            elif coefficient == -1:
                term = "-" + monomial
            else:
                term = f"{coefficient}*{monomial}"
            terms.append(term)

        if not terms:
            return "0", None

        result = terms[0]
        for term in terms[1:]:
            if term.startswith("-"):
                result += " - " + term[1:]
            else:
                result += " + " + term
        return result, None
    except Exception as exc:
        return None, repr(exc)


def parse_jones_string_to_dict(jones_string: str | None) -> Polynomial | None:
    """Parse a Jones polynomial string into a sparse exponent dictionary.

    Args:
        jones_string: Jones polynomial string to parse.

    Returns:
        Sparse polynomial keyed by exponent, or `None`.
    """
    if jones_string is None:
        return None
    text = str(jones_string).strip()
    if text == "" or text == "0":
        return {}

    text = text.replace(" - ", " + -")
    parts = [part.strip() for part in text.split(" + ") if part.strip()]
    poly: Polynomial = {}
    for term in parts:
        term = term.replace(" ", "")
        if "*t" in term:
            coeff_text, monomial = term.split("*", 1)
            coefficient = int(coeff_text)
        elif term.startswith("t") or term.startswith("-t"):
            coefficient = -1 if term.startswith("-t") else 1
            monomial = term[1:] if term.startswith("-t") else term
        else:
            coefficient = int(term)
            exponent = 0
            poly[exponent] = poly.get(exponent, 0) + coefficient
            continue

        if monomial == "t":
            exponent = 1
        elif monomial.startswith("t^"):
            exponent = int(monomial[2:])
        else:
            raise ValueError(f"Bad monomial format: {monomial}")
        poly[exponent] = poly.get(exponent, 0) + coefficient
    return {
        exponent: coefficient
        for exponent, coefficient in poly.items()
        if coefficient != 0
    }


def poly_dict_to_knotinfo_vector(poly: Polynomial | None) -> list[int] | None:
    """Convert a sparse polynomial to the workbook vector format.

    Args:
        poly: Sparse polynomial keyed by exponent.

    Returns:
        KnotInfo-style vector `[min_exp, max_exp, coeffs...]`, or `None`.
    """
    if poly is None:
        return None
    if len(poly) == 0:
        return [0, 0, 0]
    min_exp, max_exp = min(poly.keys()), max(poly.keys())
    coeffs = [
        int(poly.get(exponent, 0))
        for exponent in range(min_exp, max_exp + 1)
    ]
    return [int(min_exp), int(max_exp)] + coeffs


def jones_vector_from_pd(
    pd_list: list[list[int]],
) -> tuple[list[int] | None, str | None]:
    """Compute the workbook Jones-vector representation from a PD.

    Args:
        pd_list: Planar diagram crossing quadruples.

    Returns:
        `(vector, error)`, matching existing notebook behavior.
    """
    jones_string, error = jones_string_from_pd(pd_list)
    if error is not None:
        return None, error
    poly = parse_jones_string_to_dict(jones_string)
    vector = poly_dict_to_knotinfo_vector(poly)
    return vector, None
