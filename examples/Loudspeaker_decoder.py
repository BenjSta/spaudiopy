# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.1'
#       jupytext_version: 0.8.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
#   language_info:
#     codemirror_mode:
#       name: ipython
#       version: 3
#     file_extension: .py
#     mimetype: text/x-python
#     name: python
#     nbconvert_exporter: python
#     pygments_lexer: ipython3
#     version: 3.6.8
# ---

# %%
import numpy as np

import matplotlib.pyplot as plt
import sounddevice as sd

from spaudiopy import utils, IO, sig, decoder, sph, plots, grids


# %% User setup
setupname = "graz"
LISTEN = True

if setupname == "aalto_full":
    ls_dirs = np.array([[-18, -54, -90, -126, -162, -198, -234, -270, -306,
                         -342, 0, -72, -144, -216, -288, -45, -135, -225,
                         -315, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -10, -10, -10, -10, -10,
                         45, 45, 45, 45, 90]])
    ls_dirs[1, :] = 90 - ls_dirs[1, :]
    normal_limit = 85
    aperture_limit = 90
    opening_limit = 150
    blacklist = None
elif setupname == "aalto_partial":
    ls_dirs = np.array([[-80, -45, 0, 45, 80, -60, -30, 30, 60],
                        [0, 0, 0, 0, 0, 60, 60, 60, 60]])
    ls_dirs[1, :] = 90 - ls_dirs[1, :]
    normal_limit = 85
    aperture_limit = 90
    opening_limit = 150
    blacklist = None
elif setupname == "graz":
    ls_dirs = np.array([[0, 23.7, 48.2, 72.6, 103.1, -100.9, -69.8, -44.8, -21.4,
                         22.7, 67.9, 114.2, -113.3, -65.4, -22.7,
                         46.8, 133.4, -133.4, -43.4],
                        [90.0, 89.6, 89.4, 89.3, 89.4, 89.4, 89.6, 89.5, 89.5,
                         61.5, 61.5, 62.1, 61.6, 61.5, 62.0,
                         33.0, 33.0, 33.4, 32.3]])
    # [90, 90, 90, 90, 90, 90, 90, 90, 90, 60, 60, 60, 60, 60, 60, 30, 30, 30, 30]])
    normal_limit = 85
    aperture_limit = 90
    opening_limit = 135
    blacklist = None
else:
    raise ValueError

ls_x, ls_y, ls_z = utils.sph2cart(utils.deg2rad(ls_dirs[0, :]),
                                  utils.deg2rad(ls_dirs[1, :]))

listener_position = [0, 0, 0]


# %% Show setup
ls_setup = decoder.LoudspeakerSetup(ls_x, ls_y, ls_z, listener_position)
ls_setup.pop_triangles(normal_limit, aperture_limit, opening_limit, blacklist)

ls_setup.show()
plots.hull_normals(ls_setup)

# Test source location
src = np.array([1, 0.5, 2.5])
src_azi, src_colat, _ = utils.cart2sph(*src.tolist())

# %% VBAP
gains_vbap = decoder.vbap(src, ls_setup)


# %% Ambisonic decoding
# Ambisonic setup
N_e = ls_setup.get_characteristic_order()
ls_setup.setup_for_ambisonic(N_kernel=10)

# Show ALLRAP hulls
plots.hull(ls_setup.ambisonics_hull, title='Ambisonic hull')
plots.hull(ls_setup.kernel_hull, title='Kernel hull')

# ALLRAP
gains_allrap = decoder.allrap(src, ls_setup, N_sph=N_e)
# ALLRAP2
gains_allrap2 = decoder.allrap2(src, ls_setup, N_sph=N_e)
# ALLRAD
input_F_nm = sph.sh_matrix(N_e, src_azi, src_colat, 'real').T  # SH dirac
out_allrad = decoder.allrad(input_F_nm, ls_setup, N_sph=N_e)
out_allrad2 = decoder.allrad2(input_F_nm, ls_setup, N_sph=N_e)

utils.test_diff(gains_allrap, out_allrad, msg="ALLRAD and ALLRAP:")
utils.test_diff(gains_allrap2, out_allrad2, msg="ALLRAD2 and ALLRAP2:")

# Nearest Loudspeaker
gains_nls = decoder.nearest_loudspeaker(src, ls_setup)

# %% test multiple sources
_grid, _weights = grids.load_Fliege_Maier_nodes(10)
G_vbap = decoder.vbap(_grid, ls_setup)
G_allrap = decoder.allrap(_grid, ls_setup)
G_allrap2 = decoder.allrap2(_grid, ls_setup)

# %% Look at some measures
plots.decoder_performance(ls_setup, 'NLS')
plots.decoder_performance(ls_setup, 'VBAP')
plots.decoder_performance(ls_setup, 'VBAP', retain_outside=True)
plt.suptitle('VBAP with imaginary loudspeaker')
plots.decoder_performance(ls_setup, 'ALLRAP')
plots.decoder_performance(ls_setup, 'ALLRAP2')

# %% Binauralize
fs = 44100
hrirs = IO.load_hrirs(fs)

l_vbap_ir, r_vbap_ir = ls_setup.binauralize(ls_setup.loudspeaker_signals(
                                            gains_vbap), fs)

l_allrap_ir, r_allrap_ir = ls_setup.binauralize(ls_setup.loudspeaker_signals(
                                                gains_allrap), fs)
l_allrap2_ir, r_allrap2_ir = ls_setup.binauralize(ls_setup.loudspeaker_signals(
                                                  gains_allrap2), fs)

l_nls_ir, r_nls_ir = ls_setup.binauralize(ls_setup.loudspeaker_signals(
                                          gains_nls), fs)


# %%
fig, axs = plt.subplots(5, 1)
axs[0].plot(hrirs.nearest_hrirs(src_azi, src_colat)[0])
axs[0].plot(hrirs.nearest_hrirs(src_azi, src_colat)[1])
axs[0].set_title("hrir")
axs[1].plot(l_vbap_ir)
axs[1].plot(r_vbap_ir)
axs[1].set_title("binaural VBAP")
axs[2].plot(l_allrap_ir)
axs[2].plot(r_allrap_ir)
axs[2].set_title("binaural ALLRAP")
axs[3].plot(l_allrap2_ir)
axs[3].plot(r_allrap2_ir)
axs[3].set_title("binaural ALLRAP2")
axs[4].plot(l_nls_ir)
axs[4].plot(r_nls_ir)
axs[4].set_title("binaural NLS")
for ax in axs:
    ax.grid(True)
plt.tight_layout()

# Listen to some
s_in = sig.MonoSignal.from_file('../data/piano_mono.flac', fs)
s_in.trim(2.6, 6)

s_out_vbap = sig.MultiSignal([s_in.filter(l_vbap_ir),
                              s_in.filter(r_vbap_ir)],
                             fs=fs)
s_out_allrap = sig.MultiSignal([s_in.filter(l_allrap_ir),
                                s_in.filter(r_allrap_ir)],
                               fs=fs)
s_out_allrap2 = sig.MultiSignal([s_in.filter(l_allrap2_ir),
                                s_in.filter(r_allrap2_ir)],
                                fs=fs)
s_out_hrir = sig.MultiSignal([s_in.filter(
                                  hrirs.nearest_hrirs(src_azi, src_colat)[0]),
                              s_in.filter(
                                  hrirs.nearest_hrirs(src_azi, src_colat)[1])],
                             fs=fs)
if LISTEN:
    print("input")
    sd.play(s_in.signal,
            int(s_in.fs))
    sd.wait()
    print("hrir")
    sd.play(s_out_hrir.get_signals().T,
            int(s_in.fs))
    sd.wait()
    print("vbap")
    sd.play(s_out_vbap.get_signals().T,
            int(s_in.fs))
    sd.wait()
    print("allrap")
    sd.play(s_out_allrap.get_signals().T,
            int(s_in.fs))
    sd.wait()
    print("allrap2")
    sd.play(s_out_allrap2.get_signals().T,
            int(s_in.fs))
    sd.wait()

    fig = plt.figure()
    fig.add_subplot(5, 1, 1)
    plt.plot(s_in.signal)
    plt.grid(True)
    plt.title("dry")
    fig.add_subplot(5, 1, 2)
    plt.plot(s_out_hrir.get_signals().T)
    plt.grid(True)
    plt.title("hrir")
    fig.add_subplot(5, 1, 3)
    plt.plot(s_out_vbap.get_signals().T)
    plt.grid(True)
    plt.title("binaural VBAP")
    fig.add_subplot(5, 1, 4)
    plt.plot(s_out_allrap.get_signals().T)
    plt.grid(True)
    plt.title("binaural ALLRAP")
    fig.add_subplot(5, 1, 5)
    plt.plot(s_out_allrap2.get_signals().T)
    plt.grid(True)
    plt.title("binaural ALLRAP2")
    plt.tight_layout()

# Auralize with SSR-BRS renderer
IO.write_ssr_brirs_loudspeaker('allrap_brirs.wav',
                               ls_setup.loudspeaker_signals(gains_allrap2),
                               ls_setup, fs)

plt.show()
