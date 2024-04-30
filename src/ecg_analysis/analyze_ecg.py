#!/usr/bin/python3

# Copyright (C) 2024  Steven Trabert
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import argparse
#from datetime import datetime as dt
import sys

import folium
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DEFAULT_THRESHOLD = 50
DEFAULT_AXIS_LIMIT = 1.0


def cleanll(a):
    """remove rows that contain None values

    Parameters
    ----------
    a : ndarray
        The input array that may contain rows with None values

    Returns
    -------
    ndarray
        array without the rows that had None values
    """

    # pylint: disable=singleton-comparison
    return a[np.logical_not((a == None).any(axis=1)), :]


def analyze(rrfile, ecgfile, locfile=None, axislimit=DEFAULT_AXIS_LIMIT, threshold=DEFAULT_THRESHOLD):
    K = 32 # SDΔRR measured over 2K + 1 samples of RR first differences.

    try:
        arr_p = pd.read_csv(rrfile, sep=";")
    except OSError as e:
        print(f"Error while parsing Polar RR file: {e}")
        sys.exit(1)

    time_p = pd.to_datetime(arr_p["Phone timestamp"])
    rr_p = arr_p["RR-interval [ms]"]
    npts = len(time_p)

#   Estimate the standard deviation of the RR interval
#   differences from inner quartile range (or other
#   subset of the data) for robustness to outliers.
#   This metric, "SDΔRR", is similar to RMSSD.
    rrdiff=np.diff(rr_p, prepend=np.nan)
    sigma_p = np.full(npts, np.nan)
    for idx in range(K, npts-K):
        per25, per75 = np.percentile(rrdiff[idx-K:idx+K], [25, 75])
        sigma_p[idx] = (per75 - per25) / 1.349

    #print(*sigma_p, sep="\n")

    try:
        arr_e = pd.read_csv(ecgfile, sep=";")
    except OSError as e:
        print(f"Error while parsing Polar ECG file: {e}")
        sys.exit(1)

    ecgtime = pd.to_datetime(arr_e["Phone timestamp"])
    ecguv = arr_e["ecg [uV]"]

    fig, ax = plt.subplots(3, 1, figsize=(24, 12), layout="constrained", sharex=True)
    ax[0].xaxis.grid(True)
    ax[0].yaxis.grid(True)
    ax[0].scatter(time_p,rr_p,marker='x')
    ax[0].set_ylabel("RR(msec)", fontsize=12)
    ax[1].xaxis.grid(True)
    ax[1].yaxis.grid(True)
    ax[1].plot(time_p,sigma_p)
    ax[1].set_ylabel("SDΔRR(msec)", fontsize=12)
    ax[2].xaxis.grid(True)
    ax[2].yaxis.grid(True)
    ax[2].plot(ecgtime,ecguv)
    ax[2].set_xlabel("time", fontsize=12)
    ax[2].set_ylabel(R"ECG($\mu$v)", fontsize=12)
    ax[0].set_title(f"{rrfile}, {ecgfile}", fontsize=14)
    plt.show()

    if locfile:
        try:
            arr_l = pd.read_csv(locfile, sep=",")
        except OSError as e:
            print(f"Error while parsing location file: {e}")
            sys.exit(1)

        time_l = pd.to_datetime(arr_l["time"])
        latlon_l = arr_l[["lat", "lon"]]
        sigma_l = np.interp(time_l, time_p, sigma_p)

#        fig, ax = plt.subplots(1, 1, figsize=(24, 12), layout="constrained", sharex=True)
#        ax.xaxis.grid(True)
#        ax.yaxis.grid(True)
#        ax.plot(time_p,sigma_p)
#        ax.set_xlabel("time", fontsize=12)
#        ax.set_ylabel("SDΔRR(msec)", fontsize=12)
#        #ax.scatter(list(range(len(sigma_l))), sigma_l, marker='+', c='r')
#        ax.scatter(time_l, sigma_l, marker='+', c='r')
#        plt.show()

    warn = sigma_p > threshold
    warn = np.insert(warn, 0, False)
    warn = np.append(warn, False)
    indices = np.nonzero(np.diff(warn))[0]
    warns = np.reshape(indices, (int(len(indices)/2),2))
    time_pn = time_p.to_numpy()
    durations = np.diff(time_pn[warns])/np.timedelta64(1, 's')
    longds = durations >= 20
    qualified_warn_indices_p =warns[longds[:,0]]
    if len(qualified_warn_indices_p) > 0:
        print("Suspicious events found in " + rrfile, file=sys.stderr)

        if locfile:
            eventmap = folium.Map()
            folium.PolyLine(cleanll(np.array(latlon_l))).add_to(eventmap)
            eventmap.fit_bounds(eventmap.get_bounds(), padding=(10, 10))

        figno = 0
        for w in qualified_warn_indices_p:
            wstart = time_p[w[0]]
            wend = time_p[w[1]]
            deltat = (wend - wstart) / np.timedelta64(1, 's')
            print(f"warning from {wstart} to {wend}, duration {deltat} seconds.")

            if locfile:
                lats = np.interp(time_p[w[0]:w[1]].to_numpy().view('int'), time_l.astype(int), latlon_l['lat'])
                lons = np.interp(time_p[w[0]:w[1]].to_numpy().view('int'), time_l.astype(int), latlon_l['lon'])
                subset = np.column_stack((lats,lons))

                folium.PolyLine(cleanll(subset), color="red").add_to(eventmap)
                folium.Circle(subset[0, :], color="red", fill=True, radius=10).add_to(eventmap)
                folium.Circle(subset[-1, :], color="green", fill=True, radius=10).add_to(eventmap)

            fig, ax = plt.subplots(figsize=(10, 10), layout="constrained")
            rr_p_subset = rr_p[np.logical_and(time_p>= wstart, time_p <= wend)]
            x = rr_p_subset[0:-2]
            y = rr_p_subset[1:-1]
            ax.scatter(x, y)
            ax.plot(x, y, alpha=0.1)
            ax.set(xlim=(0, axislimit * 1000), ylim=(0, axislimit * 1000))
            ax.set_title(
                "\n".join(
                    [
                        "Poincaré Plot",
                        rrfile,
                        f"{wstart} to {wend}",
                        f"Duration: {deltat} seconds, "
                        + r"$\overline{HR}$"
                        + f": {1000.0*60.0*len(x)/sum(x):.1f} bpm",
                    ]
                ),
                fontsize=14,
            )
            ax.set_xlabel(r"$RR_{n}(msec)$", fontsize=12)
            ax.set_ylabel(r"$RR_{n+1}(msec)$", fontsize=12)
            ax.xaxis.grid(True)
            ax.yaxis.grid(True)

            plt.savefig(rrfile.replace(".csv", "") + "-" + str(figno) + ".png")
            plt.close(fig)

            figno += 1

            if locfile:
                eventmap.save(locfile.replace(".csv", ".html"))

def main():
    parser = argparse.ArgumentParser(
        prog="analyze_ecg",
        description="Polar Sensor Logger RR and ECG analyzer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("rrsrc", help="Input Polar RR file")
    parser.add_argument("ecgsrc", help="Input Polar ECG file")
    parser.add_argument(
        "--location",
        "-l",
        type=str,
        help="Input location file",
        default=None
    )
    parser.add_argument(
        "--axislimit",
        "-a",
        type=float,
        help="Maximum axis value for plots(seconds)",
        default=DEFAULT_AXIS_LIMIT
    )
    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        help="SDΔRR warning threshold(msec)",
        default=DEFAULT_THRESHOLD
    )
    args = parser.parse_args()
    analyze(rrfile=args.rrsrc, ecgfile=args.ecgsrc, locfile=args.location, axislimit=args.axislimit, threshold=args.threshold)


if __name__ == "__main__":
    main()
