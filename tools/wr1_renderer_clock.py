"""Complete ordinary rendering, page flip and idle admission on one clock.

Rendering or display preempted by an IRQ is an explicit unsupported boundary;
idle IRQ0/IRQ1 delivery uses the recovered handlers. No future state is applied.
"""
import copy

from wr1_graphics_work import GraphicsWork
from wr1_renderer_work import RendererWork
from wr1_idle_clock import IdleClock
from wr1_hardware_reference import run_driver


class RendererClock:
    def __init__(self,catalogue,tables,cmf,initial,names):
        self.catalogue=catalogue
        self.idle=IdleClock(catalogue,tables,cmf,initial,names)
        self.checkpoints={}

    def checkpoint(self,name):
        h=self.idle.hardware
        self.checkpoints[name]={'hardware':h.snapshot(),'cycle':round(h.observed_time()*27000)}

    def work(self,path):
        h=self.idle.hardware
        if h.interrupts['irq_check']:raise NotImplementedError('Renderer/display IRQ preemption')
        run_driver(h,path)
        # No path here acknowledges a PIC interrupt; any IRQ becoming pending
        # remains visible. Never silently treat such work as uninterrupted.
        if h.interrupts['irq_check']:raise NotImplementedError('Renderer/display IRQ preemption')

    def finish_render(self,render,post,display_state,return_cs):
        if render['tail']['death'] or post['door_state']==2:
            raise NotImplementedError('Death/exit transition after renderer')
        renderer=RendererWork(self.catalogue)
        self.result=renderer.complete(*(render[k] for k in ('initial_prefix','graphics','background','tiles','doors','matching','player','actors','actor_images','tail')))
        path,state,graphics=self.result[:3]
        self.work(path)
        self.checkpoint('renderer_return')
        work=GraphicsWork(self.catalogue)
        work.span(0xc1a9,0xc1a9) # Renderer outer RETF.
        work.span(0x3da3,0x3daa) # Ordinary path skips the exit sequence.
        work.span(0x409b,0x409f)
        self.work(work.path)
        self.checkpoint('display_entry')
        initial=copy.deepcopy(render['graphics'])
        initial.update(graphics_state=graphics,display_state=display_state,args=[state['render_page']])
        path,self.display_state=work.display_page(initial)
        self.work(path)
        self.checkpoint('display_return')
        work.path=[]
        work.span(0x17695,0x17695) # Display outer RETF 2.
        work.span(0x40a4,0x40a4)
        work.span(0x40b1,0x40b6)
        work.span(0x40cf,0x40cf)
        self.work(work.path)
        self.checkpoint('update_done')
        self.idle.pc=0x40d2
        self.idle.cs=return_cs
        self.idle.ax=0 # Successful display_page returns zero.
        self.idle.flags.update(c=False,z=((post['iteration']+1)&65535)==0)

    def until_admission(self,input_events=()):
        if 'update_done' not in self.checkpoints:raise ValueError('Rendering has not completed')
        return self.idle.until_admission(input_events=input_events)
