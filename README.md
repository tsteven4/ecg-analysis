# Polar ECG Data Analysis

This program scans ECG and RR files from the Polar Sensor Logger app by Jukka Happonen.  Location data may be optionallyincluded.  The program looks for high variability of successive beat to beat interval differences.

## Description of Operation

The standard deviation of the difference in successive RR periods, SDΔRR (milliseconds) is calculated.  This is similar to the standard metric RMSSD, however SDΔRR is estimated from a subset of the data to make it robust to outliers.
If the value of SDΔRR exceeds the threshold for a sufficient time then the zone is identified as suspicious.

If zone(s) are identified a message "Suspicious events found in ..." is printed and [Poincaré plots](https://en.wikipedia.org/wiki/Poincar%C3%A9_plot) are saved as portable network graphics (.png) files.

The program may not identify zones where evidence of an arrhythmia exists.  The program may erroneously identify zones where no arrhythmia occurred.  Artifacts in the data may make the program unreliable.  The program is not intended to identify all types of arrhythmia.  Interpretations of the validity and significance of the results is left to the user and their doctor.

```
usage: analyze_polar [-h] [--location LOCATION] [--axislimit AXISLIMIT] [--threshold THRESHOLD] rrsrc ecgsrc

Polar Sensor Logger RR and ECG analyzer

positional arguments:
  rrsrc                 Input Polar RR file
  ecgsrc                Input Polar ECG file

options:
  -h, --help            show this help message and exit
  --location LOCATION, -l LOCATION
                        Input location file (default: None)
  --axislimit AXISLIMIT, -a AXISLIMIT
                        Maximum axis value for plots(seconds) (default: 1.0)
  --threshold THRESHOLD, -t THRESHOLD
                        SDΔRR warning threshold(msec) (default: 50)
```

## Data Collection

The Polar Sensor Logger app may be used to collect ECG data.  If this is enabled it will also log the RR intervals.  The Polar H10 heart rate sensor supports collecting of ECG data.

It is not necessary to collect HRV data on your Garmin device.  However, it may be useful to extract the position data from a fit file recorded by your device.  A csv file suitable for use by this program can be created from a fit file by using [gpsbabel](https://www.gpsbabel.org).

The gpsbabel conversion relies on a style file 'fit2csv.style':
```
FIELD_DELIMITER         COMMA
RECORD_DELIMITER        NEWLINE
BADCHARS                COMMA
DATATYPE                TRACK

PROLOGUE time,lat,lon

IFIELD LOCAL_TIME,"","%Y-%m-%dT%H:%M:%S"
IFIELD LAT_DECIMAL,"","%0.6f"
IFIELD LON_DECIMAL,"","%0.6f"
```

```
gpsbael -i garmin_fit -f inputfile.fit -o xcsv,style=fit2csv.style -F locationfile.csv
```

If you are using Garmin Connect, instructions for exporting your data can be found [in the Garmin FAQs](https://support.garmin.com/en-US/?faq=W1TvTPW8JZ6LfJSfK512Q8).  Follow the instructions for "Export Original" and "Export a Timed Activity From Garmin Connect" to download your FIT file.

## Required Tools

A recent version of python 3 is required. 

You can download a python .whl file to install ecg-analysis from [github](https://github.com/tsteven4/ecg-analysis/releases).  Expand "Assets" and select the .whl file.  The "Continuous build" release on that page is continuously updated as changes are made.  The .whl file from older releases are not archived.  The version number may or may not change when it is updated.

You can install the .whl file with pip3.  Substitute the actual name of the .whl file you downloaded.  For example, from a command prompt (DOS, powershell, bash, etc.) :
```
pip3 install --upgrade ecg_analysis-0.0.1-py3-none-any.whl
```

### Windows

On windows python 3 can be downloaded from the [Microsoft Store](https://apps.microsoft.com/store/detail/python-310/9PJPW5LDXLZ5).  You may want to heed the message "WARNING: The script analyze_hrv.exe is installed in ... which is not on PATH.  Consider adding this directory to PATH ...".  Having the script directory in your path will make it easier analyze fit files from the command line.

### macOS

On macOS python 3 can be downloaded from [python.org](https://www.python.org/downloads/macos/), or installed with [Homebrew](https://brew.sh/) or [MacPorts](https://ports.macports.org/).

### Linux

On linux python3 is probably available from your distribution using your standard packaging tools, e.g. apt, dnf, ...
