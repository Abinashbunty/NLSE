import numba
import numpy as np


@numba.njit(parallel=True, fastmath=True, cache=True, boundscheck=False)
def nl_prop(
    A: np.ndarray,
    A_sq: np.ndarray,
    dz: float,
    alpha: float,
    V: np.ndarray,
    g: float,
    Isat: float,
) -> None:
    """A compiled parallel implementation to apply real space terms

    Args:
        A (np.ndarray): The field to propagate
        A_sq (np.ndarray): The field modulus squared
        dz (float): Propagation step in m
        alpha (float): Losses
        V (np.ndarray): Potential
        g (float): Interactions
        Isat (float): Saturation
    """
    A = A.ravel()
    A_sq = A_sq.ravel()
    V = V.ravel()
    for i in numba.prange(A.size):
        A[i] *= np.exp(
            dz * (-alpha / 2 + 1j * V[i] + 1j * g * A_sq[i] / (1 + A_sq[i] / Isat))
        )


@numba.njit(parallel=True, fastmath=True, cache=True, boundscheck=False)
def nl_prop_without_V(
    A: np.ndarray,
    A_sq: np.ndarray,
    dz: float,
    alpha: float,
    g: float,
    Isat: float,
) -> None:
    """A fused kernel to apply real space terms

    Args:
        A (cp.ndarray): The field to propagate
        A_sq (cp.ndarray): The field modulus squared
        dz (float): Propagation step in m
        alpha (float): Losses
        g (float): Interactions
        Isat (float): Saturation
    """
    A = A.ravel()
    A_sq = A_sq.ravel()
    for i in numba.prange(A.size):
        A[i] *= np.exp(dz * (-alpha / 2 + 1j * g * A_sq[i] / (1 + A_sq[i] / Isat)))


@numba.njit(parallel=True, fastmath=True, cache=True, boundscheck=False)
def nl_prop_c(
    A1: np.ndarray,
    A_sq_1: np.ndarray,
    A_sq_2: np.ndarray,
    dz: float,
    alpha: float,
    V: np.ndarray,
    g11: float,
    g12: float,
    Isat: float,
) -> None:
    """A fused kernel to apply real space terms
    Args:
        A1 (cp.ndarray): The field to propagate (1st component)
        A_sq_1 (cp.ndarray): The field modulus squared (1st component)
        A_sq_2 (cp.ndarray): The field modulus squared (2nd component)
        dz (float): Propagation step in m
        alpha (float): Losses
        V (cp.ndarray): Potential
        g11 (float): Intra-component interactions
        g12 (float): Inter-component interactions
        Isat (float): Saturation parameter of intra-component interaction
    """
    A1 = A1.ravel()
    A_sq_1 = A_sq_1.ravel()
    A_sq_2 = A_sq_2.ravel()
    for i in numba.prange(A1.size):
        # Losses
        A1[i] *= np.exp(dz * (-alpha / (2 * (1 + A_sq_1[i] / Isat))))
        # Potential
        A1[i] *= np.exp(dz * (1j * V[i]))
        # Interactions
        A1[i] *= np.exp(
            dz * (1j * (g11 * A_sq_1[i] / (1 + A_sq_1[i] / Isat) + g12 * A_sq_2[i]))
        )


@numba.njit(parallel=True, fastmath=True, cache=True, boundscheck=False)
def nl_prop_without_V_c(
    A1: np.ndarray,
    A_sq_1: np.ndarray,
    A_sq_2: np.ndarray,
    dz: float,
    alpha: float,
    g11: float,
    g12: float,
    Isat: float,
) -> None:
    """A fused kernel to apply real space terms
    Args:
        A1 (cp.ndarray): The field to propagate (1st component)
        A_sq_1 (cp.ndarray): The field modulus squared (1st component)
        A_sq_2 (cp.ndarray): The field modulus squared (2nd component)
        dz (float): Propagation step in m
        alpha (float): Losses
        g11 (float): Intra-component interactions
        g12 (float): Inter-component interactions
        Isat (float): Saturation parameter of intra-component interaction
    """
    A1 = A1.ravel()
    A_sq_1 = A_sq_1.ravel()
    A_sq_2 = A_sq_2.ravel()
    for i in numba.prange(A1.size):
        # Losses
        A1[i] *= np.exp(dz * (-alpha / (2 * (1 + A_sq_1[i] / Isat))))
        # Interactions
        A1[i] *= np.exp(
            dz * (1j * (g11 * A_sq_1[i] / (1 + A_sq_1[i] / Isat) + g12 * A_sq_2[i]))
        )


@numba.njit(parallel=True, fastmath=True, cache=True, boundscheck=False)
def rabi_coupling(A1: np.ndarray, A2: np.ndarray, dz: float, omega: float) -> None:
    """Apply a Rabi coupling term.
    This function implements the Rabi hopping term.
    It exchanges density between the two components.

    Args:
        A1 (np.ndarray): First field / component
        A2 (np.ndarray): Second field / component
        dz (float): Solver step
        omega (float): Rabi coupling strength
    """
    A1 = A1.ravel()
    A2 = A2.ravel()
    for i in numba.prange(A1.size):
        A1[i] += 1j * omega * A2[i] * dz


@numba.njit(parallel=True, fastmath=True, cache=True, boundscheck=False)
def vortex(
    im: np.ndarray, i: int, j: int, ii: np.ndarray, jj: np.ndarray, ll: int
) -> None:
    """Generates a vortex of charge l at a position (i,j) on the image im.

    Args:
        im (np.ndarray): Image
        i (int): position row of the vortex
        j (int): position column of the vortex
        ii (int): meshgrid position row (coordinates of the image)
        jj (int): meshgrid position column (coordinates of the image)
        l (int): vortex charge

    Returns:
        None
    """
    for i in numba.prange(im.shape[0]):
        for j in numba.prange(im.shape[1]):
            im[i, j] += np.angle(((ii[i, j] - i) + 1j * (jj[i, j] - j)) ** ll)


@numba.njit(parallel=True, fastmath=True, cache=True, boundscheck=False)
def square_mod(A: np.ndarray, A_sq: np.ndarray) -> None:
    """Compute the square modulus of the field

    Args:
        A (np.ndarray): The field
        A_sq (np.ndarray): The modulus squared of the field

    Returns:
        None
    """
    A = A.ravel()
    A_sq = A_sq.ravel()
    for i in numba.prange(A.size):
        A_sq[i] = A[i].real * A[i].real + A[i].imag * A[i].imag
