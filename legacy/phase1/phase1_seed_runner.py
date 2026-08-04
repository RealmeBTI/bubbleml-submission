#!/usr/bin/env python3
"""Run/recover additional deterministic seeds for the official Phase-1 task."""

import argparse
import json
import random
import time
from pathlib import Path

import h5py
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from neuralop.models import FNO
from torch.utils.data import ConcatDataset, DataLoader, Dataset


class DS(Dataset):
    def __init__(self, path):
        self.file = h5py.File(path, "r")
    def __len__(self):
        return self.file["temperature"].shape[0] - 1
    def __getitem__(self, i):
        x = torch.stack(tuple(torch.from_numpy(self.file[k][i]) for k in ("temperature", "velx", "vely")))
        y = torch.from_numpy(self.file["temperature"][i + 1]).unsqueeze(0)
        return x, y


class Block(nn.Module):
    def __init__(self, a, b):
        super().__init__(); self.m = nn.Sequential(nn.Conv2d(a,b,3,padding=1),nn.GELU(),nn.Conv2d(b,b,3,padding=1),nn.GELU())
    def forward(self, x): return self.m(x)


class UNet(nn.Module):
    def __init__(self, b=36):
        super().__init__(); self.p=nn.MaxPool2d(2)
        self.e1=Block(3,b); self.e2=Block(b,2*b); self.e3=Block(2*b,4*b); self.z=Block(4*b,8*b)
        self.u3=nn.ConvTranspose2d(8*b,4*b,2,2); self.d3=Block(8*b,4*b)
        self.u2=nn.ConvTranspose2d(4*b,2*b,2,2); self.d2=Block(4*b,2*b)
        self.u1=nn.ConvTranspose2d(2*b,b,2,2); self.d1=Block(2*b,b); self.o=nn.Conv2d(b,1,1)
    def forward(self,x):
        a=self.e1(x); b=self.e2(self.p(a)); c=self.e3(self.p(b)); z=self.z(self.p(c))
        z=self.d3(torch.cat((self.u3(z),c),1)); z=self.d2(torch.cat((self.u2(z),b),1))
        return self.o(self.d1(torch.cat((self.u1(z),a),1)))


def model(kind):
    return FNO(in_channels=3,out_channels=1,n_modes=(16,16),hidden_channels=64,n_layers=4) if kind=="fno" else UNet()


@torch.no_grad()
def metrics(m, loader):
    m.eval(); se=be=n=bn=0
    for x,y in loader:
        y=y.float(); e=(m(x.float())-y).square(); se+=e.sum().item(); n+=e.numel()
        mask=torch.zeros_like(e,dtype=torch.bool); mask[...,0,:]=mask[...,-1,:]=True; mask[...,:,0]=mask[...,:,-1]=True
        be+=e[mask].sum().item(); bn+=mask.sum().item()
    return {"mse":se/n,"rmse":(se/n)**.5,"boundary_rmse_outermost_grid":(be/bn)**.5}


def main():
    p=argparse.ArgumentParser(); p.add_argument("--data",type=Path,required=True); p.add_argument("--out",type=Path,required=True)
    p.add_argument("--seed",type=int,required=True); p.add_argument("--epochs",type=int,default=15); p.add_argument("--recover-seed",type=int)
    a=p.parse_args(); random.seed(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)
    train=ConcatDataset(DS(a.data/f) for f in ("Twall-100.hdf5","Twall-106.hdf5")); val=ConcatDataset((DS(a.data/"Twall-103.hdf5"),))
    g=torch.Generator().manual_seed(a.seed); tl=DataLoader(train,batch_size=4,shuffle=True,num_workers=0,generator=g); vl=DataLoader(val,batch_size=4,num_workers=0)
    for kind in ("fno","unet"):
        d=a.out/f"{kind}_seed_{a.recover_seed if a.recover_seed is not None else a.seed}"; d.mkdir(parents=True,exist_ok=True)
        m=model(kind); history=[]; started=time.perf_counter(); best=float("inf"); best_epoch=0
        if a.recover_seed is None:
            opt=torch.optim.AdamW(m.parameters(),lr=1e-4)
            for epoch in range(1,a.epochs+1):
                t=time.perf_counter(); m.train(); se=n=0
                for x,y in tl:
                    x=x.float(); y=y.float(); pred=m(x); loss=F.mse_loss(pred,y); opt.zero_grad(); loss.backward(); opt.step()
                    se+=F.mse_loss(pred.detach(),y,reduction="sum").item(); n+=y.numel()
                vm=metrics(m,vl)["mse"]; row={"epoch":epoch,"train_mse":se/n,"val_mse":vm,"epoch_seconds":time.perf_counter()-t}; history.append(row); print(kind,json.dumps(row),flush=True)
                if vm<best: best=vm; best_epoch=epoch; torch.save({"model":m.state_dict(),"epoch":epoch},d/"best.pt")
        else:
            ck=torch.load(d/"best.pt",map_location="cpu",weights_only=False); state=ck["model"]
            if kind == "unet" and any(k.startswith("enc1.") for k in state):
                names=(("enc1.net","e1.m"),("enc2.net","e2.m"),("enc3.net","e3.m"),("bottleneck.net","z.m"),("up3","u3"),("dec3.net","d3.m"),("up2","u2"),("dec2.net","d2.m"),("up1","u1"),("dec1.net","d1.m"),("head","o"))
                state={next((new+k[len(old):] for old,new in names if k.startswith(old)),k):v for k,v in state.items()}
            m.load_state_dict(state); best_epoch=ck["epoch"]
        out={"status":"completed" if a.recover_seed is None else "recovered_after_logger_interruption","seed":a.recover_seed if a.recover_seed is not None else a.seed,"model":kind,"best_epoch":best_epoch,"metrics":metrics(m,vl),"history":history,"wall_seconds":time.perf_counter()-started,"trainable_tensor_elements":sum(q.numel() for q in m.parameters()),"real_scalar_degrees_of_freedom":sum(q.numel()*(2 if q.is_complex() else 1) for q in m.parameters()),"runtime":{"torch":torch.__version__,"device":"cpu","mps_available":torch.backends.mps.is_available(),"cuda_available":torch.cuda.is_available()}}
        (d/"config.yaml").write_text(json.dumps({"model":kind,"seed":out["seed"],"epochs":a.epochs,"batch_size":4,"learning_rate":1e-4,"task":"official BubbleML notebook one-step temperature"},indent=2)+"\n")
        (d/"results.json").write_text(json.dumps(out,indent=2)+"\n")


if __name__ == "__main__": main()
