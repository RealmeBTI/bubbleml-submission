#!/usr/bin/env python3
"""Conditional rollouts for the official BubbleML temperature task."""
import json
from pathlib import Path
import h5py, numpy as np, torch, torch.nn as nn
from neuralop.models import FNO
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

class B(nn.Module):
 def __init__(s,a,b): super().__init__(); s.net=nn.Sequential(nn.Conv2d(a,b,3,padding=1),nn.GELU(),nn.Conv2d(b,b,3,padding=1),nn.GELU())
 def forward(s,x): return s.net(x)
class U(nn.Module):
 def __init__(s,b=36):
  super().__init__(); s.pool=nn.MaxPool2d(2); s.enc1=B(3,b); s.enc2=B(b,2*b); s.enc3=B(2*b,4*b); s.bottleneck=B(4*b,8*b)
  s.up3=nn.ConvTranspose2d(8*b,4*b,2,2); s.dec3=B(8*b,4*b); s.up2=nn.ConvTranspose2d(4*b,2*b,2,2); s.dec2=B(4*b,2*b); s.up1=nn.ConvTranspose2d(2*b,b,2,2); s.dec1=B(2*b,b); s.head=nn.Conv2d(b,1,1)
 def forward(s,x):
  a=s.enc1(x); b=s.enc2(s.pool(a)); c=s.enc3(s.pool(b)); z=s.bottleneck(s.pool(c)); z=s.dec3(torch.cat((s.up3(z),c),1)); z=s.dec2(torch.cat((s.up2(z),b),1)); return s.head(s.dec1(torch.cat((s.up1(z),a),1)))

def load(kind,path):
 m=FNO(in_channels=3,out_channels=1,n_modes=(16,16),hidden_channels=64,n_layers=4) if kind=="fno" else U(); state=torch.load(path,map_location="cpu",weights_only=False)["model"]
 if kind=="unet" and any(k.startswith("e1.") for k in state):
  names=(("e1.m","enc1.net"),("e2.m","enc2.net"),("e3.m","enc3.net"),("z.m","bottleneck.net"),("u3","up3"),("d3.m","dec3.net"),("u2","up2"),("d2.m","dec2.net"),("u1","up1"),("d1.m","dec1.net"),("o","head")); state={next((new+k[len(old):] for old,new in names if k.startswith(old)),k):v for k,v in state.items()}
 m.load_state_dict(state); m.eval(); return m

@torch.no_grad()
def roll(m,f,start,h):
 temp=torch.from_numpy(f["temperature"][start]).float().unsqueeze(0).unsqueeze(0)
 for j in range(h):
  t=start+j; vx=torch.from_numpy(f["velx"][t]).float().unsqueeze(0).unsqueeze(0); vy=torch.from_numpy(f["vely"][t]).float().unsqueeze(0).unsqueeze(0); temp=m(torch.cat((temp,vx,vy),1))
 return temp.squeeze().numpy()

root=Path("experiments/phase1_official"); data=Path("/private/tmp/bubbleml-phase1.QPrIg3/official_notebook_run/Twall-103.hdf5"); starts=(30,80,130); horizons=(1,5,10); rows=[]
with h5py.File(data,"r") as f:
 for seed in (7,42,123):
  for kind in ("fno","unet"):
   m=load(kind,root/f"{kind}_seed_{seed}/best.pt")
   for h in horizons:
    for start in starts:
     pred=roll(m,f,start,h); truth=f["temperature"][start+h]; err=pred-truth; edge=np.concatenate((err[0,:],err[-1,:],err[1:-1,0],err[1:-1,-1])); rows.append({"seed":seed,"model":kind,"start":start,"horizon":h,"rmse":float(np.sqrt(np.mean(err**2))),"boundary_rmse_outermost_grid":float(np.sqrt(np.mean(edge**2)))})
 # visual seed 42, horizon 10
 fm=load("fno",root/"fno_seed_42/best.pt"); um=load("unet",root/"unet_seed_42/best.pt"); fig,ax=plt.subplots(3,5,figsize=(13,8),constrained_layout=True)
 for r,start in enumerate(starts):
  truth=f["temperature"][start+10]; fp=roll(fm,f,start,10); up=roll(um,f,start,10)
  for c,z in enumerate((truth,fp,np.abs(fp-truth),up,np.abs(up-truth))): ax[r,c].imshow(np.flipud(z)); ax[r,c].set_xticks([]); ax[r,c].set_yticks([])
 for c,t in enumerate(("Truth","FNO","FNO abs. error","U-Net","U-Net abs. error")): ax[0,c].set_title(t)
 fig.savefig(root/"rollout_h10_examples.png",dpi=180); plt.close(fig)
summary={}
for kind in ("fno","unet"):
 summary[kind]={}
 for h in horizons:
  q=[r for r in rows if r["model"]==kind and r["horizon"]==h]; summary[kind][str(h)]={k:float(np.mean([x[k] for x in q])) for k in ("rmse","boundary_rmse_outermost_grid")}
(root/"rollout_results.json").write_text(json.dumps({"protocol":"autoregressive temperature with ground-truth future velocities (conditional rollout)","starts":starts,"horizons":horizons,"rows":rows,"summary":summary},indent=2)+"\n")
print(json.dumps(summary,indent=2))
