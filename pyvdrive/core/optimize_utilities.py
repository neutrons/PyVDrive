import numpy  # type: ignore
from scipy.optimize import curve_fit  # type: ignore


# Define model function to be used to fit to the data above:
def gauss(x, *p):
    """
    blabla  : Gauss + background
    :param x:
    :param p:
    :return:
    """
    A, mu, sigma, b1, b0 = p
    return A*numpy.exp(-(x-mu)**2/(2.*sigma**2)) + b1 * x + b0


def fit_gaussian(vec_x, vec_y):
    """

    :param vec_x:
    :param vec_y:
    :return:
    """
    # initial guess for the fitting coefficients (A, mu and sigma above)
    p0 = [1., 0., 1.]

    # fit
    coeff, var_matrix = curve_fit(gauss, vec_x, vec_y, p0=p0)

    # Get the fitted curve
    hist_fit = gauss(vec_x, *coeff)

    return coeff, hist_fit
