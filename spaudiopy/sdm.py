# -*- coding: utf-8 -*-
"""
@author: chris
"""
from itertools import repeat

import numpy as np
from joblib import Memory
import multiprocessing

from . import utils
from . import sig
from . import process as pcs


# Prepare Caching
cachedir = './__cache_dir'
memory = Memory(cachedir)


def render_stereoSDM(sdm_p, sdm_phi, sdm_theta):
    """Stereophonic SDM Render IR.

    Parameters
    ----------
    sdm_p : (n,) array_like
        Pressure p(t).
    sdm_phi : (n,) array_like
        Azimuth phi(t).
    sdm_theta : (n,) array_like
        Colatitude theta(t).

    Returns
    -------
    ir_l : array_like
        Left impulse response.
    ir_r : array_like
        Right impulse response.
    """
    ir_l = np.zeros(len(sdm_p))
    ir_r = np.zeros_like(ir_l)

    for i, (p, phi, theta) in enumerate(zip(sdm_p, sdm_phi, sdm_theta)):
        h_l = 0.5*(1 + np.cos(phi - np.pi/2))
        h_r = 0.5*(1 + np.cos(phi + np.pi/2))
        # convolve
        ir_l[i] += p * h_l
        ir_r[i] += p * h_r
    return ir_l, ir_r


def _render_BSDM_sample(i, p, phi, theta, hrir_l, hrir_r, grid_phi, grid_theta):
    h_l, h_r = pcs.select_hrtf(hrir_l, hrir_r, grid_phi, grid_theta,
                               phi, theta)
    # global shared_array
    shared_array[i:i + len(h_l), 0] += p * h_l
    shared_array[i:i + len(h_l), 1] += p * h_r


@memory.cache
def render_BSDM(sdm_p, sdm_phi, sdm_theta, hrirs, jobs_count=None):
    """
    Binaural SDM Render.

    Parameters
    ----------
    sdm_p : (n,) array_like
        Pressure p(t).
    sdm_phi : (n,) array_like
        Azimuth phi(t).
    sdm_theta : (n,) array_like
        Colatitude theta(t).
    hrirs : sig.HRIRs
        'None' selects default hrir set.
    jobs_count : int
        Parallel jobs, switches implementation if > 1.

    Returns
    -------
    bsdm_l : array_like
        Left impulse response.
    bsdm_r : array_like
        Right impulse response.
    """
    if jobs_count is None:
        jobs_count = multiprocessing.cpu_count()

    hrir_l = hrirs.left
    hrir_r = hrirs.right
    grid = hrirs.grid
    bsdm_l = np.zeros(len(sdm_p) + hrir_l.shape[1] - 1)
    bsdm_r = np.zeros_like(bsdm_l)
    grid_phi = np.array(grid['az'])
    grid_theta = np.array(grid['el'])

    if jobs_count == 1:
        for i, (p, phi, theta) in enumerate(zip(sdm_p, sdm_phi, sdm_theta)):
            h_l, h_r = pcs.select_hrtf(hrir_l, hrir_r, grid_phi, grid_theta,
                                       phi, theta)
            # convolve
            bsdm_l[i:i + len(h_l)] += p * h_l
            bsdm_r[i:i + len(h_r)] += p * h_r

    else:
        _shared_array_shape = np.shape(np.c_[bsdm_l, bsdm_r])
        _arr_base = _create_shared_array(_shared_array_shape)
        _arg_itr = zip(range(len(sdm_p)), sdm_p, sdm_phi, sdm_theta,
                       repeat(hrir_l), repeat(hrir_r),
                       repeat(grid_phi), repeat(grid_theta))
        # execute
        with multiprocessing.Pool(processes=jobs_count,
                                  initializer=_init_shared_array,
                                  initargs=(_arr_base,
                                            _shared_array_shape,)) as pool:
            pool.starmap(_render_BSDM_sample, _arg_itr)
        # reshape
        _result = np.frombuffer(_arr_base.get_obj()).reshape(
                                _shared_array_shape)
        bsdm_l = _result[:, 0]
        bsdm_r = _result[:, 1]

    return bsdm_l, bsdm_r


def _render_loudspeaker_sdm_sample(idx, p, g, ls_setup, hrirs):
    h_l, h_r = ls_setup.binauralize(g, hrirs.fs, hrirs=hrirs)
    # global shared_array
    shared_array[idx:idx + len(h_l), 0] += p * h_l
    shared_array[idx:idx + len(h_l), 1] += p * h_r


@memory.cache
def render_loudspeaker_sdm(sdm_p, ls_gains, ls_setup, hrirs, jobs_count=None):
    """
    Render sdm signal on loudspeaker setup as binaural synthesis.

    Parameters
    ----------
    sdm_p : (n,) array_like
        Pressure p(t).
    ls_gains : (n, l)
        Loudspeaker (l) gains.
    ls_setup : decoder.LoudspeakerSetup
    hrirs : sig.HRIRs
    jobs_count : int
        Parallel jobs, switches implementation if > 1.

    Returns
    -------
    ir_l : array_like
        Left impulse response.
    ir_r : array_like
        Right impulse response.
    """
    if jobs_count is None:
        jobs_count = multiprocessing.cpu_count()

    ir_l = np.zeros(len(sdm_p) + len(hrirs) - 1)
    ir_r = np.zeros_like(ir_l)

    if jobs_count == 1:
        for idx, (p, g) in enumerate(zip(sdm_p, ls_gains)):
            h_l, h_r = ls_setup.binauralize(g, hrirs.fs)
            # convolve
            ir_l[idx:idx + len(h_l)] += p * h_l
            ir_r[idx:idx + len(h_r)] += p * h_r

    else:
        _shared_array_shape = np.shape(np.c_[ir_l, ir_r])
        _arr_base = _create_shared_array(_shared_array_shape)
        _arg_itr = zip(range(len(sdm_p)), sdm_p, ls_gains,
                       repeat(ls_setup), repeat(hrirs))
        # execute
        with multiprocessing.Pool(processes=jobs_count,
                                  initializer=_init_shared_array,
                                  initargs=(_arr_base,
                                            _shared_array_shape,)) as pool:
            pool.starmap(_render_loudspeaker_sdm_sample, _arg_itr)
        # reshape
        _result = np.frombuffer(_arr_base.get_obj()).reshape(
                                _shared_array_shape)
        ir_l = _result[:, 0]
        ir_r = _result[:, 1]

    return ir_l, ir_r


# Parallel worker stuff -->
def _create_shared_array(shared_array_shape):
    """Allocate ctypes array from shared memory with lock."""
    d_type = 'd'
    shared_array_base = multiprocessing.Array(d_type, shared_array_shape[0] *
                                              shared_array_shape[1])
    return shared_array_base


def _init_shared_array(shared_array_base, shared_array_shape):
    """Makes 'shared_array' available to child processes."""
    global shared_array
    shared_array = np.frombuffer(shared_array_base.get_obj())
    shared_array = shared_array.reshape(shared_array_shape)
# < --Parallel worker stuff
