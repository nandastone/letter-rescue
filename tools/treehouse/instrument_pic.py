"""Add read-only paired observations around pinned PIC queue primitives."""


def instrument(source,irq=False):
    def replace(old,new):
        nonlocal source
        if source.count(old)!=1:raise ValueError('PIC hook differs: '+old[:100])
        source=source.replace(old,new)
    if irq:
        replace('void PIC_Controller::set_imr(Bit8u val) {','#include "irq_probe.h"\nvoid PIC_Controller::set_imr(Bit8u val) {')
        for signature,args in [
            ('void PIC_ActivateIRQ(Bitu irq)', '1,irq'),
            ('void PIC_DeActivateIRQ(Bitu irq)', '2,irq'),
            ('void PIC_SetIRQMask(Bitu irq, bool masked)', '3,irq,masked'),
            ('static void write_command(Bitu port,Bitu val,Bitu /*iolen*/)', '4,port,val'),
            ('static void write_data(Bitu port,Bitu val,Bitu /*iolen*/)', '5,port,val'),
            ('void PIC_runIRQs(void)', '6')]:
            replace(signature+' {',signature+' {\n\tTreehouseIrqScope trace_irq('+args+');')
        for expression in ['slave.vector_base + pic1_irq','master.vector_base + i']:
            replace('CPU_HW_Interrupt('+expression+');','TreehouseIrqVector('+expression+');\n\tCPU_HW_Interrupt('+expression+');')
    replace('static float srv_lag = 0;','static float srv_lag = 0;\n#include "pic_probe.h"')
    replace('\tPICEntry * entry=pic_queue.free_entry;\n\tif(InEventService)', '\tunsigned trace_pic=TreehousePicBegin(1,handler,delay,val);\n\tPICEntry * entry=pic_queue.free_entry;\n\tif(InEventService)')
    replace('\tAddEntry(entry);\n}', '\tAddEntry(entry);\n\tTreehousePicEnd(trace_pic);\n}')
    for name,kind,signature in [('PIC_RemoveSpecificEvents',3,'PIC_EventHandler handler, Bitu val'),('PIC_RemoveEvents',2,'PIC_EventHandler handler')]:
        start=f'void {name}({signature}) {{'
        pos=source.index(start);end=source.index('\n}\n',pos)
        body=source[pos:end]
        body=body.replace(start,start+f'\n\tunsigned trace_pic=TreehousePicBegin({kind},handler,0,'+('val' if kind==3 else '0')+');')
        source=source[:pos]+body+'\n\tTreehousePicEnd(trace_pic);'+source[end:]
    replace('bool PIC_RunQueue(void) {','bool PIC_RunQueue(void) {\n\tunsigned trace_pic_start=TreehousePicBegin(4);')
    replace('\tCPU_CycleLeft+=CPU_Cycles;\n\tCPU_Cycles=0;\n\tif (CPU_CycleLeft<=0)', '\tCPU_CycleLeft+=CPU_Cycles;\n\tCPU_Cycles=0;\n\tTreehousePicEnd(trace_pic_start);\n\tif (CPU_CycleLeft<=0)')
    replace('\t\tPICEntry * entry=pic_queue.next_entry;\n\t\tpic_queue.next_entry=entry->next;', '\t\tPICEntry * entry=pic_queue.next_entry;\n\t\tunsigned trace_pic_service=TreehousePicBegin(5,entry->pic_event,entry->index,entry->value);\n\t\tpic_queue.next_entry=entry->next;')
    replace('\t\tsrv_lag = entry->index;\n\t\t(entry->pic_event)', '\t\tsrv_lag = entry->index;\n\t\tTreehousePicEnd(trace_pic_service);\n\t\t(entry->pic_event)')
    replace('\t/* Check when to set the new cycle end */', '\tunsigned trace_pic_end=TreehousePicBegin(6);\n\t/* Check when to set the new cycle end */')
    replace('\tCPU_CycleLeft-=CPU_Cycles;\n\tif (PIC_IRQCheck)', '\tCPU_CycleLeft-=CPU_Cycles;\n\tTreehousePicEnd(trace_pic_end);\n\tif (PIC_IRQCheck)')
    replace('void TIMER_AddTick(void) {', 'void TIMER_AddTick(void) {\n\tunsigned trace_pic_tick=TreehousePicBegin(7);')
    replace('\t/* Call our list of ticker handlers */','\tTreehousePicEnd(trace_pic_tick);\n\t/* Call our list of ticker handlers */')
    return source
