from Compiler.mpc_math import log_fx
from Compiler.mpc_math import cos
from Compiler.mpc_math import sin
from Compiler.mpc_math import sqrt
import math
from Compiler import mpc_math, util
from Compiler.types import *
from Compiler.types import _unreduced_squant
from Compiler.library import *
from Compiler.util import is_zero, tree_reduce
from Compiler.comparison import CarryOutRawLE
from Compiler.GC.types import sbitint
from functools import reduce

e = math.e
pi = math.pi


def gen_samples_(d):

    # print_ln("generating samples")

    assert d >= 1

    gaussian_vec = sfix.Array(d)

    # div two since the Box-Mueller transform produces 2 samples
    @for_range_opt(d // 2)
    def _(i):
        A = sfix.get_random(0, 1)
        B = sfix.get_random(0, 1)

        C = sqrt(-2 * log_fx(A, e))

        trig_arg = (2 * pi) * B
        cosine = cos(trig_arg)
        sine = sin(trig_arg)

        r1 = C * cosine
        r2 = C * sine

        gaussian_vec[2 * i] = r1
        gaussian_vec[(2 * i) + 1] = r2

    # if d is odd, our vec is one element short. Obtain one more sample
    if d % 2 == 1:
        gaussian_vec[d - 1] = gen_samples_(2)[0]

    return gaussian_vec
#### end


def normalize_(vec, d):

    # print_ln("normalizing samples")

    L2_norm_vec_intermediate = sfix.Array(d)
    L2_norm_vec_intermediate.assign_vector(vec * vec)

    global s
    s = sfix._new(0)

    @for_range(d)
    def _(i):
        global s
        s += L2_norm_vec_intermediate[i]

    L2_norm = sqrt(s)

    L2_norm_vec = sfix.Array(d)
    L2_norm_vec.assign_vector(L2_norm_vec_intermediate / L2_norm)

    return L2_norm_vec
#### end


# exponential distribution with rate 1 (Exp(1))
def generate_exp_distribution_():
    U = sfix.get_random(0, 1)
    exp_sample = -1 * log_fx(U, e)
    return exp_sample
#### end


def gen_gamma_dis2_(d, n, epsilon=1, lamb=1):

    # print_ln("generating gamma dis samples")

    global final_gamma
    final_gamma = sfix._new(0)

    @for_range_opt(d)
    def _(i):
        global final_gamma
        final_gamma = final_gamma + generate_exp_distribution_()

    norm_const = n * epsilon * lamb
    div = 2/norm_const

    final_gamma = final_gamma * div

    # print_ln("%s", final_gamma.reveal())

    return final_gamma
#### end


def gen_noise(d, n, epsilon=1, lamb=1):

    gaussian_vec = gen_samples_(d)
    gaussian_vec_normalized = normalize_(gaussian_vec, d)

    #### added by sikha
    gamma = gen_gamma_dis2_(d, n, epsilon, lamb)
    noise_vector = sfix.Array(d)
    noise_vector.assign_vector(gaussian_vec_normalized.get_vector() * gamma)

    return noise_vector
#### end


# d_ = 1700
# n_ = 1800
# epsilon_ = 1
# lamb_ = 1
#
# noise_vector = gen_noise(d_, n_, epsilon_, lamb_)
#
# print_ln("%s", noise_vector.reveal()[:20])
