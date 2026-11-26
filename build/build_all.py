#!/usr/bin/env python3
import json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'build')); sys.path.insert(0,str(ROOT/'build'/'lib'))
from world import build_world
from economy import build as build_economy
from build_data import Terrarium
from nation import build as build_nation
from resources import build as build_resources
from lenses import build as build_lenses
from counties import build as build_counties
from people import build as build_people
from districts import build as build_districts
from infrastructure import build as build_infrastructure
from wonders import build as build_wonders

if __name__=='__main__':
    t=time.time()
    terr=Terrarium()
    wm=build_world(terr, ROOT/'build'/'cache')
    eco=build_economy(wm)
    nation=build_nation(eco['nation_core'])
    res=build_resources(wm, eco['cities'], eco['states'])
    lenses=build_lenses(wm, eco['cities'], eco['states'], res)
    counties=build_counties(eco['cities'], wm['world'])
    citizens=build_people(eco['cities'], nation['nation'])
    districts=build_districts(eco['cities'], nation)
    infra=build_infrastructure(wm, eco['cities'])
    wonders=build_wonders(wm, eco['cities'])
    print('total',round(time.time()-t,1),'s')
