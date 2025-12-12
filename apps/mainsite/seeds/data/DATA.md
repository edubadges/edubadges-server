# Data

The data originates at the EWI "PBA". 

CSVs can be found on https://gitlab.surf.nl/eduwallet/pba/-/tree/main/source/edu?ref_type=heads

The PBA CSV lacks data that we need, but which is added by this PBA repo when generating json files.

Get the latest versions at:
```bash
curl -s https://pba.dev.eduwallet.nl/mbob.json > pba_mbob.json
curl -s https://pba.dev.eduwallet.nl/tun.json > pba_tun.json
curl -s https://pba.dev.eduwallet.nl/hbot.json > pba_hbot.json 
curl -s https://pba.dev.eduwallet.nl/uvh.json > pba_uvh.json 
```

For the dev.eduwallet.nl domain, an EDUVPN is needed to access them. 

At https://pba.playground.eduwallet.nl/ public versions are available, but they
may have different values than the dev versions that we fetched and committed.

We don't want to fetch them on-the-fly as that creates a dependency on a service
we don't control and which may not be accessible. So fetch and commit the
correct versions.