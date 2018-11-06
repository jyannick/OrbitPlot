from datetime import datetime, timezone

import orekit
import numpy as np
import pandas as pd

from orekit.pyhelpers import setup_orekit_curdir, absolutedate_to_datetime, datetime_to_absolutedate
from org.orekit.propagation.analytical.tle import TLE, TLEPropagator
from org.orekit.frames import FramesFactory
from org.orekit.bodies import OneAxisEllipsoid
from org.orekit.utils import IERSConventions, Constants
from org.orekit.orbits import KeplerianOrbit
from org.orekit.forces.maneuvers import SmallManeuverAnalyticalModel
from org.orekit.propagation.events import DateDetector
from org.orekit.attitudes import LofOffset
from org.orekit.frames import LOFType
from org.hipparchus.geometry.euclidean.threed import Vector3D
from org.orekit.propagation.analytical import AdapterPropagator

print("Initializing Orekit")
orekit.initVM()
setup_orekit_curdir()
INERTIAL_FRAME = FramesFactory.getEME2000()


def propagate(tle_line1, tle_line2, duration, step, maneuvers=[]):
    tle = create_tle(tle_line1, tle_line2)
    tle_propagator = TLEPropagator.selectExtrapolator(tle)
    propagator_with_maneuvers = AdapterPropagator(tle_propagator)

    # TODO works only for chronological maneuvers, because of the "propagate" to get the state
    for maneuver in maneuvers:
        date, frame, deltaV, isp = maneuver
        propagator_with_maneuvers.addEffect(SmallManeuverAnalyticalModel(propagator_with_maneuvers.propagate(datetime_to_absolutedate(date)),
                                                                         frame, deltaV, isp))

    ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
    earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
                             Constants.WGS84_EARTH_FLATTENING,
                             ITRF)

    time = [tle.getDate().shiftedBy(float(dt)) \
            for dt in np.arange(0, duration, step)]
    orbits = [KeplerianOrbit(propagator_with_maneuvers.propagate(date).getOrbit()) for date in time]

    subpoints = [
        earth.transform(propagator_with_maneuvers.propagate(date).getPVCoordinates(), tle_propagator.getFrame(), date)
        for date in time]
    return pd.DataFrame({'time': [absolutedate_to_datetime(orbit.getDate()) for orbit in orbits],
                         'a': [orbit.getA() for orbit in orbits],
                         'e': [orbit.getE() for orbit in orbits],
                         'i': [orbit.getI() for orbit in orbits],
                         'pom': [orbit.getPerigeeArgument() for orbit in orbits],
                         'RAAN': [orbit.getRightAscensionOfAscendingNode() for orbit in orbits],
                         'v': [orbit.getTrueAnomaly() for orbit in orbits],
                         'ex': [orbit.getEquinoctialEx() for orbit in orbits],
                         'ey': [orbit.getEquinoctialEy() for orbit in orbits],
                         'hx': [orbit.getHx() for orbit in orbits],
                         'hy': [orbit.getHy() for orbit in orbits],
                         'latitude': [np.degrees(gp.getLatitude().getReal()) for gp in subpoints],
                         'longitude': [np.degrees(gp.getLongitude().getReal()) for gp in subpoints]})


def create_tle(tle_line1, tle_line2):
    return TLE(tle_line1.strip(), tle_line2.strip())


if __name__ == "__main__":
    spot5_1 = " 1 27421U 02021A   02124.48976499 -.00021470  00000-0 -89879-2 0    20"
    spot5_2 = " 2 27421  98.7490 199.5121 0001333 133.9522 226.1918 14.26113993    62"

    maneuvers = [(datetime(2002, month=5, day=5, hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc),
                  FramesFactory.getEME2000(), Vector3D(100., 0., 0.), 300.),
                 (datetime(2002, month=5, day=6, hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc),
                  FramesFactory.getEME2000(), Vector3D(0., 100., 0.), 300.),
                 (datetime(2002, month=5, day=7, hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc),
                  FramesFactory.getEME2000(), Vector3D(0., 0., 100.), 300.)
                 ]

    ephemeris = propagate(spot5_1, spot5_2, 5 * 86400, 60, maneuvers)
    print(ephemeris)
