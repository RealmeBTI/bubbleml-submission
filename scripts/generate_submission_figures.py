#!/usr/bin/env python3
"""Generate vector PDF/SVG and 600-DPI PNG figures from stored JSON evidence."""

from __future__ import annotations

import argparse
import html
import json
import random
from pathlib import Path
from statistics import fmean

from PIL import Image, ImageDraw, ImageFont
from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, Rect, String
from reportlab.lib.colors import HexColor


ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 720, 480


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def bootstrap(values: list[float], seed: int) -> tuple[float, float]:
    rng = random.Random(seed)
    means = sorted(fmean(rng.choice(values) for _ in values) for _ in range(10_000))
    return means[249], means[9749]


class Figure:
    def __init__(self, width: int = WIDTH, height: int = HEIGHT) -> None:
        self.width, self.height = width, height
        self.commands: list[tuple] = []

    def line(self, x1, y1, x2, y2, color="#111827", width=1.0, dash=None):
        self.commands.append(("line", x1, y1, x2, y2, color, width, dash))

    def polyline(self, points, color="#111827", width=1.5):
        self.commands.append(("polyline", list(points), color, width))

    def text(self, x, y, value, size=11, anchor="start", color="#111827", rotate=0):
        self.commands.append(("text", x, y, str(value), size, anchor, color, rotate))

    def circle(self, x, y, radius=4, fill="#2563eb", stroke="#2563eb"):
        self.commands.append(("circle", x, y, radius, fill, stroke))

    def rect(self, x, y, width, height, fill="#ffffff", stroke=None):
        self.commands.append(("rect", x, y, width, height, fill, stroke))

    def save(self, base: Path) -> None:
        base.parent.mkdir(parents=True, exist_ok=True)
        drawing = Drawing(self.width, self.height)
        for command in self.commands:
            kind = command[0]
            if kind == "line":
                _, x1, y1, x2, y2, color, width, dash = command
                item = Line(x1, self.height-y1, x2, self.height-y2, strokeColor=HexColor(color), strokeWidth=width)
                if dash:
                    item.strokeDashArray = dash
                drawing.add(item)
            elif kind == "polyline":
                _, points, color, width = command
                flipped = [(x, self.height-y) for x, y in points]
                drawing.add(PolyLine(flipped, strokeColor=HexColor(color), strokeWidth=width, fillColor=None))
            elif kind == "text":
                _, x, y, value, size, anchor, color, rotate = command
                text_anchor = {"start": "start", "middle": "middle", "end": "end"}[anchor]
                item = String(x, self.height-y, value, fontName="Helvetica", fontSize=size, fillColor=HexColor(color), textAnchor=text_anchor)
                if rotate:
                    item.angle = rotate
                drawing.add(item)
            elif kind == "circle":
                _, x, y, radius, fill, stroke = command
                drawing.add(Circle(x, self.height-y, radius, fillColor=HexColor(fill), strokeColor=HexColor(stroke)))
            elif kind == "rect":
                _, x, y, width, height, fill, stroke = command
                drawing.add(Rect(x, self.height-y-height, width, height, fillColor=HexColor(fill) if fill else None, strokeColor=HexColor(stroke) if stroke else None))
        renderPDF.drawToFile(drawing, str(base.with_suffix(".pdf")))
        renderSVG.drawToFile(drawing, str(base.with_suffix(".svg")))

        scale = 600 / 72
        image = Image.new("RGB", (round(self.width*scale), round(self.height*scale)), "white")
        draw = ImageDraw.Draw(image)
        font_path = "/System/Library/Fonts/Helvetica.ttc"
        fonts: dict[int, ImageFont.FreeTypeFont] = {}
        def font(size):
            key = max(7, round(size*scale))
            if key not in fonts:
                fonts[key] = ImageFont.truetype(font_path, key)
            return fonts[key]
        for command in self.commands:
            kind = command[0]
            if kind == "line":
                _, x1, y1, x2, y2, color, width, dash = command
                if dash:
                    length = max(abs(x2-x1), abs(y2-y1))
                    segments = max(1, int(length/8))
                    for index in range(0, segments, 2):
                        t1, t2 = index/segments, min(1, (index+1)/segments)
                        draw.line((round((x1+(x2-x1)*t1)*scale), round((y1+(y2-y1)*t1)*scale), round((x1+(x2-x1)*t2)*scale), round((y1+(y2-y1)*t2)*scale)), fill=color, width=max(1, round(width*scale)))
                else:
                    draw.line(tuple(round(v*scale) for v in (x1,y1,x2,y2)), fill=color, width=max(1, round(width*scale)))
            elif kind == "polyline":
                _, points, color, width = command
                draw.line([(round(x*scale), round(y*scale)) for x,y in points], fill=color, width=max(1, round(width*scale)), joint="curve")
            elif kind == "text":
                _, x, y, value, size, anchor, color, rotate = command
                if rotate:
                    # Axis labels are rendered horizontally in the raster fallback.
                    value = value
                pil_anchor = {"start": "la", "middle": "ma", "end": "ra"}[anchor]
                draw.text((round(x*scale), round(y*scale)), value, font=font(size), fill=color, anchor=pil_anchor)
            elif kind == "circle":
                _, x, y, radius, fill, stroke = command
                draw.ellipse(tuple(round(v*scale) for v in (x-radius,y-radius,x+radius,y+radius)), fill=fill, outline=stroke, width=max(1,round(scale)))
            elif kind == "rect":
                _, x, y, width, height, fill, stroke = command
                draw.rectangle(tuple(round(v*scale) for v in (x,y,x+width,y+height)), fill=fill, outline=stroke)
        image.save(base.with_suffix(".png"), dpi=(600, 600))


def axes(fig: Figure, title: str, xlabel: str, ylabel: str, bounds: tuple[float,float,float,float], area=(85,55,690,410)):
    left, top, right, bottom = area
    xmin, xmax, ymin, ymax = bounds
    fig.text((left+right)/2, 25, title, 15, "middle")
    fig.text((left+right)/2, 454, xlabel, 11, "middle")
    fig.text(left, 44, ylabel, 9, "start")
    fig.line(left, bottom, right, bottom, width=1.2)
    fig.line(left, top, left, bottom, width=1.2)
    for index in range(6):
        yy = top + (bottom-top)*index/5
        value = ymax - (ymax-ymin)*index/5
        fig.line(left, yy, right, yy, color="#d1d5db", width=0.6)
        fig.text(left-8, yy+4, f"{value:.3g}", 8, "end")
    for index in range(6):
        xx = left + (right-left)*index/5
        value = xmin + (xmax-xmin)*index/5
        fig.text(xx, bottom+17, f"{value:.3g}", 8, "middle")
    def project(x, y):
        return left+(x-xmin)/(xmax-xmin)*(right-left), bottom-(y-ymin)/(ymax-ymin)*(bottom-top)
    return project


def figure_pareto(output: Path) -> None:
    phase1 = load("benchmark_results/phase1_gpu_decisive_tfno_unet_n11/benchmark_results.json")
    hybrid = load("benchmark_results/tier1_hybrid_n11/benchmark_results.json")
    divergence = load("benchmark_results/lambda_sensitivity_030_n11/benchmark_results.json")
    specs = [("T-FNO",phase1,"tfno","#2563eb"),("U-Net",phase1,"unet","#dc2626"),("Hybrid (lambda=0)",hybrid,"hybrid_tfno","#7c3aed"),("Hybrid (lambda=0.30)",divergence,"hybrid_div","#059669")]
    rows=[]
    for index,(label,payload,model,color) in enumerate(specs):
        raw=payload["raw_seed_metrics"][model]
        xs=[float(raw[s]["mass_conservation_mae"]) for s in sorted(raw,key=int)]
        ys=[float(raw[s]["interface_temperature_rmse"]) for s in sorted(raw,key=int)]
        rows.append((label,fmean(xs),fmean(ys),bootstrap(xs,100+index),bootstrap(ys,200+index),color))
    fig=Figure(); fig.rect(0,0,WIDTH,HEIGHT)
    project=axes(fig,"Tutorial-split interface/conservation trade-off","Mass-conservation MAE (lower is better)","Interface-temperature RMSE",(0.075,0.225,14.65,15.75))
    for index,(label,x,y,(xl,xh),(yl,yh),color) in enumerate(rows):
        px,py=project(x,y); p1,_=project(xl,y); p2,_=project(xh,y); _,q1=project(x,yl); _,q2=project(x,yh)
        fig.line(p1,py,p2,py,color,width=1.4); fig.line(px,q1,px,q2,color,width=1.4); fig.circle(px,py,4.5,color,color)
        lx=470; ly=70+20*index; fig.line(lx,ly,lx+24,ly,color,width=2); fig.circle(lx+12,ly,3,color,color); fig.text(lx+32,ly+4,label,9)
    fig.save(output/"fig1_pareto_front")


def figure_dry(output: Path) -> None:
    payload=load("benchmark_results/phase4_chf_rollout/rollout_results.json"); signals=payload["signals"]
    times=[float(v) for v in signals["timesteps"]]; all_values=[float(v) for key in ("ground_truth","tfno","unet") for v in signals[key]]
    ymin,ymax=min(all_values)-.02,max(all_values)+.02
    fig=Figure(); fig.rect(0,0,WIDTH,HEIGHT); project=axes(fig,"Tutorial Twall-100 autoregressive rollout","Source timestep","Heater-adjacent dry-area fraction",(min(times),max(times),ymin,ymax))
    for index,(label,key,color) in enumerate((("Ground truth","ground_truth","#111827"),("T-FNO","tfno","#2563eb"),("U-Net","unet","#dc2626"))):
        fig.polyline([project(t,float(v)) for t,v in zip(times,signals[key],strict=True)],color,1.4)
        fig.line(490,70+20*index,514,70+20*index,color,2); fig.text(522,74+20*index,label,9)
    threshold=float(payload["event_definition"]["event_dry_fraction_threshold"]); x1,y=project(min(times),threshold); x2,_=project(max(times),threshold); fig.line(x1,y,x2,y,"#6b7280",1,[5,4])
    fig.save(output/"fig2_dry_area_trace")


def figure_lambda(output: Path) -> None:
    payload=load("benchmark_results/lambda_sensitivity/lambda_sensitivity_results.json"); lambdas=[float(v) for v in payload["candidates"]]
    specs=(("validation_mse","Validation MSE"),("validation_spectral_divergence_mae","Spectral divergence MAE"),("validation_interface_temperature_rmse","Interface-temp. RMSE"))
    fig=Figure(1080,360); fig.rect(0,0,1080,360); fig.text(540,22,"Three-seed divergence-penalty sensitivity",15,"middle")
    for panel,(metric,label) in enumerate(specs):
        left=60+panel*350; top=48; right=330+panel*350; bottom=300
        rows=[payload["candidates"][f"{v:.10g}"]["metrics"][metric] for v in lambdas]; lows=[float(r["bootstrap_ci95_low"]) for r in rows]; highs=[float(r["bootstrap_ci95_high"]) for r in rows]; means=[float(r["mean"]) for r in rows]
        ymin,ymax=min(lows),max(highs); pad=.08*(ymax-ymin or 1); ymin-=pad; ymax+=pad
        def project(x,y): return left+(x-min(lambdas))/(max(lambdas)-min(lambdas))*(right-left), bottom-(y-ymin)/(ymax-ymin)*(bottom-top)
        fig.text((left+right)/2,342,"lambda_div",9,"middle"); fig.text(left,38,label,10)
        fig.line(left,bottom,right,bottom); fig.line(left,top,left,bottom)
        for i in range(4):
            yy=top+(bottom-top)*i/3; val=ymax-(ymax-ymin)*i/3; fig.line(left,yy,right,yy,"#d1d5db",.5); fig.text(left-5,yy+3,f"{val:.3g}",7,"end")
        points=[]
        for x,mean,low,high in zip(lambdas,means,lows,highs,strict=True):
            px,py=project(x,mean); _,pl=project(x,low); _,ph=project(x,high); fig.line(px,pl,px,ph,"#2563eb",1); fig.circle(px,py,3,"#2563eb","#2563eb"); points.append((px,py)); fig.text(px,bottom+14,f"{x:.2g}",7,"middle")
        fig.polyline(points,"#2563eb",1.2)
        selected=float(payload["selected_lambda_div"]); sx,_=project(selected,ymin); fig.line(sx,top,sx,bottom,"#dc2626",1,[4,3])
    fig.save(output/"fig3_lambda_sensitivity")


def figure_losses(output: Path) -> None:
    root=ROOT/"experiments/phase1_gpu_decisive"; models=("fno","tfno","ffno","unet"); seeds=(42,100,1234,2025,9999); colors=("#2563eb","#dc2626","#059669","#7c3aed","#d97706")
    fig=Figure(900,660); fig.rect(0,0,900,660); fig.text(450,24,"Phase 1 validation histories",15,"middle")
    for index,model in enumerate(models):
        col=index%2; row=index//2; left=70+col*430; right=430+col*430; top=52+row*290; bottom=290+row*290
        histories=[]
        for seed in seeds:
            data=json.loads((root/f"{model}_seed_{seed}"/"results.json").read_text())["history"]; histories.append((seed,[float(v["epoch"]) for v in data],[float(v["val_mse"]) for v in data]))
        xmin=0; xmax=max(max(x) for _,x,_ in histories); ymin=min(min(y) for _,_,y in histories); ymax=max(max(y) for _,_,y in histories); pad=.05*(ymax-ymin or 1); ymin-=pad; ymax+=pad
        def project(x,y): return left+(x-xmin)/(xmax-xmin or 1)*(right-left), bottom-(y-ymin)/(ymax-ymin)*(bottom-top)
        fig.text((left+right)/2,top-10,model.upper().replace("TFNO","T-FNO").replace("FFNO","F-FNO"),11,"middle"); fig.line(left,bottom,right,bottom); fig.line(left,top,left,bottom)
        for seed,xs,ys in histories: fig.polyline([project(x,y) for x,y in zip(xs,ys,strict=True)],colors[seeds.index(seed)],1)
        fig.text((left+right)/2,bottom+20,"Epoch",8,"middle"); fig.text(left-6,top+5,f"{ymax:.3g}",7,"end"); fig.text(left-6,bottom,f"{ymin:.3g}",7,"end")
    fig.save(output/"fig4_loss_curves")


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--output-dir",type=Path,default=Path("submission/figures")); args=parser.parse_args(); output=args.output_dir if args.output_dir.is_absolute() else ROOT/args.output_dir
    figure_pareto(output); figure_dry(output); figure_lambda(output); figure_losses(output); print(f"Generated four PDF/SVG/600-DPI PNG figure families in {output}")


if __name__ == "__main__": main()
