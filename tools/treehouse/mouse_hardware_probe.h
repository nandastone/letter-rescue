// Appended only to the isolated pinned mouse.cpp capture build. No mutation.
#include <stdint.h>
extern "C" void TreehouseReadMouseHardware(uint32_t* out){
    for(unsigned i=0;i<96;i++)out[i]=0;
    out[0]=mouse.events;out[1]=mouse.in_UIR;out[2]=mouse.sub_mask;
    out[3]=mouse.sub_seg;out[4]=mouse.sub_ofs;out[5]=(uint16_t)POS_X;out[6]=(uint16_t)POS_Y;
    out[7]=(uint16_t)(Bit16s)mouse.mickey_x;out[8]=(uint16_t)(Bit16s)mouse.mickey_y;
    out[9]=mouse.hidden;out[10]=AllowINT33RMAccess();out[11]=useps2callback;out[12]=mouse.timer_in_progress;
    out[13]=Real2Phys(CALLBACK_RealPointer(int74_ret_callback));out[14]=Real2Phys(uir_callback);out[15]=mouse.inhibit_draw;
    for(unsigned i=0;i<QUEUE_SIZE;i++){out[16+2*i]=mouse.event_queue[i].type;out[17+2*i]=mouse.event_queue[i].buttons;}
}
