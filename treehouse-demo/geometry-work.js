"use strict";
// Resident rectangle, clipping and short memory helpers used by animations.
// Arrays hold unsigned 16-bit words; comparisons follow signed 8086 branches.
class OriginalGeometryWork {
  static singleStrings=new Set([0x824f,0x8253,0x8254,0x8258,0x8259,0x825d,0x825e,0x8262,0x8209,0x820b,0x8536,0x8538,0x853a,0x853c,0x098a,0x09b8].map(a=>'resident:'+a.toString(16).padStart(4,'0')));
  static *instructions(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16).padStart(4,'0');}
  static signed(n){return (n<<16)>>16;}
  static wordSlice(array,start,length){return new Proxy(Array(length).fill(0),{get:(target,key)=>typeof key==='string'&&/^\d+$/.test(key)?array[start+Number(key)]:Reflect.get(target,key),set:(target,key,value)=>{if(typeof key==='string'&&/^\d+$/.test(key)){array[start+Number(key)]=value&65535;return true;}return Reflect.set(target,key,value);}});}
  static *storeWords(address,out,offset,count,value){
    let remaining=count,at=offset;
    do{
      yield* this.instructions(address);const done=yield {call:'rep-store-words',address,remaining};
      if(!Number.isInteger(done)||done<0||done>remaining||(remaining&&done===0))throw new Error('Invalid geometry REP progress');
      for(let i=0;i<done;i++)out[at++]=value&65535;remaining-=done;
    }while(remaining);
  }
  static *offset(a,dy,dx,out=[0,0,0,0]){
    const emit=this.instructions;yield* emit(0x8242,0x8243,0x8245,0x8246,0x8247,0x8248,0x824b,0x824e);
    for(const [i,load,add,store] of [[0,0x824f,0x8250,0x8253],[1,0x8254,0x8255,0x8258],[2,0x8259,0x825a,0x825d],[3,0x825e,0x825f,0x8262]]){
      yield* emit(load);let value=a[i];yield* emit(add);value=(value+(i%2?dx:dy))&65535;yield* emit(store);out[i]=value;
    }
    yield* emit(0x8263,0x8264,0x8266,0x8267,0x8268,0x8269,0x826a);return out;
  }
  static *intersection(a,b,out=[0,0,0,0]){
    const emit=this.instructions,s16=this.signed;yield* emit(0x83b4,0x83b5,0x83b7,0x83b8,0x83b9,0x83bc,0x83bf,0x83c3,0x83c6);
    let left=s16(b[1]);if(left<s16(a[1])){yield* emit(0x83c8);left=s16(a[1]);}
    yield* emit(0x83cb,0x83cf,0x83d2);let right=s16(b[3]);if(right>s16(a[3])){yield* emit(0x83d4);right=s16(a[3]);}
    yield* emit(0x83d7,0x83d9);let nonempty=false;
    if(left<right){
      yield* emit(0x83db,0x83de);out[1]=left&65535;yield* emit(0x83e1);out[3]=right&65535;
      yield* emit(0x83e4,0x83e7,0x83ea,0x83ec);let top=s16(b[0]);if(top<s16(a[0])){yield* emit(0x83ee);top=s16(a[0]);}
      yield* emit(0x83f0,0x83f4,0x83f7);let bottom=s16(b[2]);if(bottom>s16(a[2])){yield* emit(0x83f9);bottom=s16(a[2]);}
      yield* emit(0x83fc,0x83fe);nonempty=top<bottom;
      if(nonempty){yield* emit(0x8400,0x8403);out[0]=top&65535;yield* emit(0x8405);out[2]=bottom&65535;yield* emit(0x8408,0x840b);}
    }
    if(!nonempty){yield* emit(0x840d,0x840f,0x8412);yield* this.storeWords(0x8415,out,0,4,0);}
    yield* emit(0x8417,0x8418,0x8419,0x841a);return {rect:out,nonempty};
  }
  static *empty(rect){
    const emit=this.instructions,s16=this.signed;yield* emit(0x7ee6,0x7ee7,0x7ee9,0x7eec,0x7eef,0x7ef3,0x7ef7);
    let empty=s16(rect[1])>=s16(rect[3]);
    if(!empty){yield* emit(0x7ef9,0x7efc,0x7f00);empty=s16(rect[0])>=s16(rect[2]);if(!empty)yield* emit(0x7f02);}
    yield* emit(0x7f04,0x7f05);return empty;
  }
  static *union(a,b,out=[0,0,0,0]){
    const emit=this.instructions,s16=this.signed;yield* emit(0x84fa,0x84fb,0x84fd,0x84fe,0x84ff,0x8500,0x8503);
    const values=[];
    for(const [i,load,cmp,branch,move] of [[0,0x8506,0x8509,0x850b,0x850d],[1,0x850f,0x8513,0x8516,0x8518],[2,0x851b,0x851f,0x8522,0x8524],[3,0x8527,0x852b,0x852e,0x8530]]){
      yield* emit(load,cmp,branch);let value=s16(b[i]);if(i<2?value>s16(a[i]):value<s16(a[i])){yield* emit(move);value=s16(a[i]);}values[i]=value&65535;
    }
    yield* emit(0x8533,0x8536);out[0]=values[0];yield* emit(0x8537,0x8538);out[1]=values[1];yield* emit(0x8539,0x853a);out[2]=values[2];yield* emit(0x853b,0x853c);out[3]=values[3];
    yield* emit(0x853d,0x8540,0x8542,0x8543,0x8544,0x8545,0x8546);return out;
  }
  static *localPoint(point,surface,out=[0,0]){
    const emit=this.instructions;yield* emit(0x81f0,0x81f1,0x81f3,0x81f4,0x81f8,0x81fb,0x81fe);const y=(point[0]-surface[2])&65535;
    yield* emit(0x8201,0x8203);const x=(point[1]-surface[3])&65535;yield* emit(0x8206,0x8209);out[0]=y;yield* emit(0x820a,0x820b);out[1]=x;
    yield* emit(0x820c,0x820f,0x8211,0x8212,0x8213);return out;
  }
  static *clipPush(surface,rect,stack){
    const emit=this.instructions;yield* emit(0x7db6,0x7dba,0x7dbd,0x7dc0,0x7dc1,0x7dc2,0x7dc3);
    const saved=[];for(let i=3;i>=0;i--){yield* emit(0x7dc4,0x7dc7);saved[i]=surface[12+i];yield* emit(0x7dca);}stack.push(saved);
    yield* emit(0x7dcc,0x7dcd,0x7dce,0x7dcf,0x7dd0,0x7dd1,0x7dd2,0x7dd3,0x7dd5,0x7dd8,0x7dd9,0x7ddb,0x7dde,0x7de0,0x7de2);
    if(rect===null){yield* emit(0x7de4,0x7de7,0x7de8);yield* this.storeWords(0x7de9,surface,12,4,0);yield* emit(0x7deb);}
    else{
      yield* emit(0x7ded,0x7df0,0x7df1,0x7df2,0x7df3,0x7df4,0x7df7,0x7df8,0x7df9,0x7dfc,0x7dfd,0x7dfe,0x7dff);
      const bottom=yield {call:'point-local',point:rect.slice(2,4),surface};yield* emit(0x7e02,0x7e03);
      const top=yield {call:'point-local',point:rect.slice(0,2),surface};yield* emit(0x7e06,0x7e07,0x7e08,0x7e09,0x7e0a,0x7e0b,0x7e0c,0x7e0d);
      const result=yield {call:'rectangle-intersection',a:[...top,...bottom],b:Array.from(surface.slice(12,16)),out:this.wordSlice(surface,12,4)};
      for(let i=0;i<4;i++)surface[12+i]=result.rect[i];
    }
    yield* emit(0x7e10,0x7e13,0x7e15,0x7e16,0x7e18,0x7e19);return rect;
  }
  static *clipPop(surface,stack){
    const emit=this.instructions;if(!stack.length)throw new Error('Empty original clip stack');const saved=stack.pop();
    yield* emit(0x7e1c,0x7e1d,0x7e1e,0x7e22,0x7e25);
    for(let i=0;i<4;i++){yield* emit(0x7e28);surface[12+i]=saved[i];yield* emit(0x7e2a,0x7e2d);}
    yield* emit(0x7e2f,0x7e30,0x7e31);
  }
  static *clear(color,rect){
    const emit=this.instructions;yield* emit(0x7f08,0x7f09,0x7f0b,0x7f0e,0x7f0f,0x7f10,0x7f13,0x7f14,0x7f17,0x7f18);
    yield {call:'rectangle-fill',mode:0,color,rect};yield* emit(0x7f1b,0x7f1c);
  }
  static *nearCopy(memory,source,destination,length,{sourceBytes=null}={}){
    const emit=this.instructions;if(memory.length!==65536)throw new Error('Near memory must contain one segment');
    yield* emit(0x096e,0x096f,0x0971,0x0973,0x0975,0x0977,0x0979,0x097c,0x097f,0x0981,0x0984);
    let count=length&65535,si=source&65535,di=destination&65535;
    if(sourceBytes!==null&&sourceBytes.length<count)throw new Error('Short literal near-copy source');
    const read=at=>sourceBytes===null?memory[at]:sourceBytes[(at-source)&65535];
    if(count){
      yield* emit(0x0986,0x0988);if(di&1){yield* emit(0x098a);memory[di]=read(si);di=(di+1)&65535;si=(si+1)&65535;yield* emit(0x098b);count--;}
      yield* emit(0x098c);
      for(const [address,size,remaining0] of [[0x098e,2,count>>>1],[0x0992,1,count&1]]){
        let remaining=remaining0;do{
          yield* emit(address);const done=yield {call:size===2?'rep-move-words':'rep-move-bytes',address,remaining};
          if(!Number.isInteger(done)||done<0||done>remaining||(remaining&&done===0))throw new Error('Invalid near-copy REP progress');
          for(let i=0;i<done;i++){
            const low=read(si),high=size===2?read((si+1)&65535):0;memory[di]=low;if(size===2)memory[(di+1)&65535]=high;si=(si+size)&65535;di=(di+size)&65535;
          }remaining-=done;
        }while(remaining);
        if(size===2)yield* emit(0x0990);
      }
    }
    yield* emit(0x0994,0x0996,0x0998,0x0999);return destination&65535;
  }
  static *nearFill(memory,destination,length,value){
    const emit=this.instructions;if(memory.length!==65536)throw new Error('Near memory must contain one segment');
    yield* emit(0x099a,0x099b,0x099d,0x099f,0x09a1,0x09a3,0x09a6,0x09a8,0x09ab);let count=length&65535,di=destination&65535;value&=255;
    if(count){
      yield* emit(0x09ad,0x09b0,0x09b2,0x09b6);if(di&1){yield* emit(0x09b8);memory[di]=value;di=(di+1)&65535;yield* emit(0x09b9);count--;}
      yield* emit(0x09ba);
      for(const [address,size,remaining0] of [[0x09bc,2,count>>>1],[0x09c0,1,count&1]]){
        let remaining=remaining0;do{
          yield* emit(address);const done=yield {call:size===2?'rep-store-words':'rep-store-bytes',address,remaining};
          if(!Number.isInteger(done)||done<0||done>remaining||(remaining&&done===0))throw new Error('Invalid near-fill REP progress');
          for(let i=0;i<done*size;i++){memory[di]=value;di=(di+1)&65535;}remaining-=done;
        }while(remaining);
        if(size===2)yield* emit(0x09be);
      }
    }
    yield* emit(0x09c2,0x09c4,0x09c5,0x09c6);return destination&65535;
  }
}
