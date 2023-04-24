import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import random
from .shell_primary_number import SHELL_PRIMARY_NUMS


# read wf file
def read_wf(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    data = [list(map(float, line.strip().split())) for line in lines if len(line.strip().split()) == 2]
    return np.asarray(data)


def read_info(filename='Fdata/info.dat'):
    """
    {'H': {
        'number': 1,
        'nshell': 1,
        'shells': [0, 1],
        'occupation': [1.0, 0.0],
    }}
    :param filename:
    :return: dict
    """
    with open(filename, 'r') as f:
        lines = f.readlines()

    result_dict = {}

    status = 0  # 0: start block, 1: in block
    for il, line in enumerate(lines):
        content = line.strip()
        if len(content) == 0:
            continue
        if content == '=' * 70:
            if status == 0:
                status = 1
            elif status == 1:
                status = 0

        if status == 1:
            result_dict[lines[il + 2].strip().split()[0]] = {
                'number': int(lines[il+1].strip()),
                'nshell': int(lines[il + 5].strip().split()[0]),
                'shells': [int(i) for i in lines[il + 6].strip().split()],
                'occupation': [int(i) for i in lines[il + 7].strip().split()],
            }
            status = 0
        else:
            continue

    return result_dict


# gaussian function
def gaussian(r, n=1, A=np.array([1]), a=np.array([1])):
    f = np.sum([Ai * r ** (n - 1) * np.exp(-ai * r ** 2)
                for Ai, ai in zip(A, a)], axis=0)
    return f


# loss function
def loss_function(x, *args):
    len_x = int(len(x) / 2)
    A = x[0:len_x]
    a = x[len_x:]
    n, r, Y = args
    if r.shape != Y.shape:
        raise ValueError('Shapes for args[1] and args[2] are not equal!')
    loss = np.abs(Y - gaussian(r, n, A, a)).sum()
    return loss


def fit_wf(data, n=1, tol=None, Nzeta=None, bnds=None):
    """

    :param data: shape = [N, 2]
    :param n: principal quantum number
    :param tol: Error tolerance
    :param Nzeta: number of gaussian
    :param bnds: boundary for fitting
    :return:
    """
    R, Y = np.asarray(data)
    if Nzeta is None:
        if tol is None:
            tol = 1.0E-5
        Nzeta0 = 3  # initial zeta number
        Nzeta = 20  # so the maximum Nzeta is 20
    else:
        Nzeta0 = Nzeta

    success = False
    for nz in range(Nzeta0, Nzeta+1):
        A0 = np.random.rand(nz)  # initial value for A
        a0 = np.random.rand(nz)  # initial value for alpha0
        x0 = np.concatenate([A0, a0])  # initial para vector
        if bnds is not None:
            bnds = [bnds[0]] * nz + [bnds[1]] * nz
        res = minimize(loss_function, x0, bounds=bnds, args=(n, R, Y))
        Ae = res.x[0:nz]
        ae = res.x[nz:]
        Y_fit = gaussian(R, n, Ae, ae)
        error = (np.linalg.norm(Y-Y_fit))/len(Y)
        if tol is not None:
            if error < tol:
                success = True
                break

    if not success:
        if tol is None:
            print("Fitting error is {} for {} gaussians.".format(error, Nzeta))
        else:
            print("Warning: Fitting error {} didn't meet the tolerance {} for {} gaussians.".format(error, tol, Nzeta))

    return [Ae, ae, Y_fit]


def plot_fitting(data, Ae, ae, output=None):
    R, Y = np.asarray(data)
    plt.plot(R, Y, '-')
    plt.plot(R, gaussian(R, n, Ae, ae))
    for Ai, ai in zip(Ae, ae):
        plt.plot(R, gaussian(R, n, [Ai], [ai]))
    if output is not None:
        plt.savefig(output)
    else:
        plt.show()


if "__name__" == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog='FitBasisSet',
        description='Fit Fireball basis set to Gaussian-type basis set.',)

    # 判断 Fdata/info.dat 是否存在，需要从里面读取 shell 数目



# main
# filename = '../tests/test_utils_fit_basis_set/001.wf-s0.dat'
filename = '../tests/test_utils_fit_basis_set/007.wf-p1.dat'

n = 1
data = read_wf(filename)
bnds = None

Ae, ae, Y_fit = fit_wf(data=data.T, n=n, bnds=bnds, tol=1.0E-2)
plot_fitting(data.T, Ae, ae, output=None)

print("Done")
