import glob, os, pickle, numpy as np, vtk, cadquery as cq
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
from PIL import Image, ImageDraw, ImageFont
FR='/home/claude/wt_frame5/cad/v14/frame/world/'; DK='/home/claude/wt_deck5/cad/v14/deck/world/'; SC='/home/claude/wt_all/cad/v14/scoop/world/'
def names(d): return [os.path.basename(f)[:-5] for f in sorted(glob.glob(d+'*.step'))]
K=[n for n in names(DK) if 'assembly' not in n]; S=[n for n in names(SC) if 'assembly' not in n]; F=names(FR)
iso_p=('201','202','203','204','205','206','207','47b','48_','49b','50_','54_','55_','56_','NEMA17_drum','reuse_62','reuse_63')
idn_p=('210','211','212','213','214','215','216','217','218','MG996R_scanner','dummy_USB_webcam')
ele_p=('225','226','227','228','dummy_','leg_')
G={'wood':[(FR,n) for n in F if n[:3] in ('100','101','102','103','104','105','106','107','109')],
   'deck':[(FR,n) for n in F if n.startswith('108')],
   'isolate':[(DK,n) for n in K if n.startswith(iso_p)],
   'identify':[(DK,n) for n in K if n.startswith(idn_p)],
   'indicate':[(SC,n) for n in S]+[(DK,n) for n in K if n.startswith('220')],
   'electronics':[(DK,n) for n in K if n.startswith(ele_p) and not n.startswith('dummy_USB_webcam')],
   'roof':[(FR,n) for n in F if n.startswith(('114','130','131'))]}
left=[n for n in K if not any(n.startswith(p) for p in iso_p+idn_p+ele_p+('220',))]; print('unassigned deck parts:',left)
if os.path.exists('m.pkl'): M=pickle.load(open('m.pkl','rb'))
else:
    M={}
    for g,l in G.items():
        for d,n in l:
            v,t=cq.importers.importStep(d+n+'.step').val().tessellate(0.5,0.4)
            M[(d,n)]=(np.array([[p.x,p.y,p.z] for p in v]),np.array(t))
    pickle.dump(M,open('m.pkl','wb'))
def actor(V,T,col,op=1.0):
    pts=vtk.vtkPoints(); pts.SetData(numpy_to_vtk(V.astype(float),deep=True))
    ca=vtk.vtkCellArray(); ca.SetCells(len(T), numpy_to_vtkIdTypeArray(np.hstack([np.full((len(T),1),3),T]).ravel().astype(np.int64),deep=True))
    pd=vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(ca)
    nm=vtk.vtkPolyDataNormals(); nm.SetInputData(pd); nm.SetFeatureAngle(40)
    mp=vtk.vtkPolyDataMapper(); mp.SetInputConnection(nm.GetOutputPort()); mp.ScalarVisibilityOff()
    a=vtk.vtkActor(); a.SetMapper(mp); p=a.GetProperty(); p.SetColor(*col); p.SetOpacity(op); p.SetSpecular(0.15); return a
WOOD=(0.84,0.70,0.48)
def render(groups,fn,size=(1000,820)):
    ren=vtk.vtkRenderer(); ren.SetBackground(1,1,1); ren.SetUseDepthPeeling(1); ren.SetMaximumNumberOfPeels(8)
    for g,col,op in groups:
        for key in G[g]: ren.AddActor(actor(*M[key],col,op))
    lk=vtk.vtkLightKit(); lk.AddLightsToRenderer(ren)
    c=ren.GetActiveCamera(); c.SetFocalPoint(0,0,300); c.SetPosition(520,1500,900); c.SetViewUp(0,0,1); c.SetViewAngle(29); ren.ResetCameraClippingRange()
    w=vtk.vtkRenderWindow(); w.SetOffScreenRendering(1); w.SetAlphaBitPlanes(1); w.SetMultiSamples(0); w.AddRenderer(ren); w.SetSize(*size); w.Render()
    g=vtk.vtkWindowToImageFilter(); g.SetInput(w); g.Update(); wr=vtk.vtkPNGWriter(); wr.SetFileName(fn); wr.SetInputConnection(g.GetOutputPort()); wr.Write()
base=[('wood',WOOD,0.35),('deck',(0.93,0.87,0.72),0.30)]
panels=[('1. Wood frame','posts, rails, cleats, floor and deck ply',[('wood',WOOD,1.0),('deck',(0.93,0.87,0.72),1.0)]),
 ('2. Frame + ISOLATE','hopper, chute, drum, 2 vibration trays (on the deck)',base+[('isolate',(0.16,0.55,0.85),1.0)]),
 ('3. Frame + IDENTIFY','scanner plate, trapdoors, camera bridge + webcam, LEDs',base+[('identify',(0.95,0.55,0.10),1.0)]),
 ('4. Frame + INDICATE','scoop on its beam (under the deck) + drop funnel',base+[('indicate',(0.20,0.68,0.30),1.0)]),
 ('5. Frame + electronics','PSU, Pi and driver trays (on the deck, along the back)',base+[('electronics',(0.55,0.35,0.75),1.0)]),
 ('6. Everything + roof and studs','all stages together',[('wood',WOOD,1.0),('deck',(0.93,0.87,0.72),1.0),('isolate',(0.16,0.55,0.85),1.0),('identify',(0.95,0.55,0.10),1.0),('indicate',(0.20,0.68,0.30),1.0),('electronics',(0.55,0.35,0.75),1.0),('roof',(0.80,0.12,0.12),0.35)])]
B=lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',s); Fn=lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',s)
sheet=Image.new('RGB',(3000,1900),'white'); d=ImageDraw.Draw(sheet)
d.text((40,20),'Bricked Sorting V14: one stage at a time on the wood frame (seen from the front)',fill='black',font=B(44))
for i,(t,sub,gr) in enumerate(panels):
    render(gr,'_p.png'); im=Image.open('_p.png'); x=(i%3)*1000; y=100+(i//3)*900
    sheet.paste(im,(x,y+70)); d.text((x+40,y),t,fill='black',font=B(36)); d.text((x+40,y+46),sub,fill=(60,60,60),font=Fn(26))
sheet.save('stages.png'); print('done')
