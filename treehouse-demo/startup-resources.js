"use strict";
// Resource ownership for the pinned VGA/Sound Blaster launch profile. Inputs
// come from executable/configuration/archive bytes and the DOS environment.
// Boundary observers are optional; no native state drives this sequence.
class OriginalStartupResources {
  static create({startup,builtins,pixelsPerByte,savedRectangle,archives,volume,soundRateLimits,firstFileHandle=5},observe=()=>{}){
    if(archives.length<2)throw new Error("Original startup archives are incomplete");
    const state=OriginalResourceStartup.memory(startup),m=state.memory;
    state.soundRateLimits=soundRateLimits;
    state.embeddedAssets=builtins;
    state.builtins=new OriginalResourceLoading(m,0,{observeWork:false,embeddedCatalog:true});
    state.catalogs=new OriginalCatalogLoading(m);
    const emit=(stage,phase)=>observe(stage,phase,state);
    const font=state.builtins.source('builtin:FONT:0',builtins.FONT.payload,builtins.FONT.flags);
    emit('font-activation',0);OriginalFontLoading.activate(state.builtins,font);emit('font-activation',1);
    state.font=font;state.cursor=new OriginalCursorLoading(state.builtins,pixelsPerByte);
    emit('cursor-source',0);state.cursor.loadSource('builtin:CURS:0',builtins.CURS.payload,builtins.CURS.flags);emit('cursor-source',1);
    emit('cursor-activation',0);state.cursor.activate();emit('cursor-activation',1);
    state.saved=new OriginalSavedSurface(m,{bounds:savedRectangle,pixelsPerByte});
    let fileHandle=firstFileHandle;
    const open=archive=>{
      emit('catalog',0);const id=state.catalogs.open({...archive,volume,fileHandle:fileHandle++});emit('catalog',1);return id;
    };
    const thHandle=open(archives[0]),th=state.catalogs.catalogs.get(thHandle);
    state.cursor.loader=th.loader;
    emit('cursor-source',0);state.cursor.source=state.catalogs.loadSource(thHandle,'CURS',1);emit('cursor-source',1);
    emit('cursor-activation',0);state.cursor.activate();emit('cursor-activation',1);
    state.gameFont=state.catalogs.loadSource(thHandle,'FONT',1);
    emit('font-activation',0);OriginalFontLoading.activate(th.loader,state.gameFont);emit('font-activation',1);
    state.available=m.available();
    const sound=th.records.find(e=>e.tag===''&&e.id===1);
    if(!sound)throw new Error("Original sound configuration is missing");
    state.direct=new OriginalDirectLoading(m,{observeWork:false});
    state.soundConfiguration=state.direct.load({payload:sound.payload,catalogHandle:thHandle,cachedHandle:sound.handle});
    for(const archive of archives.slice(1))open(archive);
    emit('startup-sound',0);
    state.backgroundSound=this.loadSound(state,0);m.retain(state.backgroundSound);
    emit('startup-sound',1);
    return state;
  }
  static loadSound(state,id,rateLimits=state.soundRateLimits||{}){
    const found=state.catalogs.resolve('SND',id);if(!found)return 0;
    const {catalog,entry}=found,handle=state.catalogs.loadSource(catalog.handle,'SND',id);
    const sound=new OriginalSoundLoading(state.memory,catalog.handle,{observeWork:false});
    const prepared=sound.prepare(handle,entry.payload,rateLimits);
    return prepared.action==='missing'?0:handle;
  }
  static prepareTitle(state,{backgroundPalette,animationPalette,backgroundBounds,animationOrigin,sound,script},observe=()=>{}){
    // Main 350 followed by overlay 5:206..308. Resource IDs, palette masks,
    // rectangles and script code are extracted from the pinned program/data.
    const m=state.memory,c=state.catalogs,palettes=new OriginalPaletteLoading(c);
    const emit=stage=>observe(stage,state);
    state.driverSound=this.loadSound(state,65535);emit('driver-sound');
    const background=palettes.load(backgroundPalette.id,backgroundPalette.banks);emit('background-palette');
    m.freeHandle(this.loadShape(state,background,1));emit('background-drawn');
    const [top,left,bottom,right]=backgroundBounds;
    state.titleSurface={rows:m.near.allocate(2*(bottom-top)),pixels:m.allocateRaw((right-left)*(bottom-top)),bounds:[...backgroundBounds]};
    emit('title-surface');
    m.freeHandle(this.loadShape(state,background,2));m.freeHandle(background);emit('background-released');
    state.titlePalette=palettes.load(animationPalette.id,animationPalette.banks);emit('title-palette');
    state.titleSound=this.loadSound(state,sound);m.lock(state.titleSound);emit('title-sound');
    return this.prepareTitleAnimation(state,{id:animationPalette.id,script,origin:animationOrigin},observe);
  }
  static loadShape(state,palette,relative){
    const data=state.memory.resourcePayloads.get(palette),id=(data[0]|data[1]<<8)+relative-1;
    const found=state.catalogs.resolve('SHAP',id);if(!found)throw new Error("Missing original shape");
    return state.catalogs.loadShape(found.catalog.handle,id,palette);
  }
  static selectCursor(state,id){
    const c=state.catalogs,found=c.resolve('CURS',id);
    if(found){state.cursor.loader=found.catalog.loader;state.cursor.source=c.loadSource(found.catalog.handle,'CURS',id);}
    else if(id===0){
      const asset=state.embeddedAssets.CURS;state.cursor.loader=state.builtins;
      state.cursor.loadSource('builtin:CURS:0',asset.payload,asset.flags);
    }else throw new Error("Missing original cursor");
    state.cursor.activate();
  }
  static prepareTitleAnimation(state,{id,script,origin},observe=()=>{}){
    if(state.titleAnimation&&!state.titleAnimation.disposed)throw new Error("Title animation is still owned");
    const m=state.memory,c=state.catalogs;
    this.selectCursor(state,1);
    const found=c.resolve('SCR',id);if(!found)throw new Error("Missing title script");
    state.titleScript=state.direct.load({payload:found.entry.payload,catalogHandle:found.catalog.handle,cachedHandle:found.entry.handle});
    const bounds=[...script.bounds],height=bounds[2]-bounds[0],width=bounds[3]-bounds[1],[x,y]=origin;
    bounds[0]=y-height;bounds[2]=y;bounds[1]=x-Math.floor(width/2);bounds[3]=bounds[1]+width;
    const data=m.resourcePayloads.get(state.titlePalette),last=data[2]|data[3]<<8;
    observe('animation-before',state);
    state.titleAnimation=OriginalAnimationMemory.prepare(m,{script:{...script,bounds},last,paletteHandle:state.titlePalette,loadShape:relative=>this.loadShape(state,state.titlePalette,relative)});
    state.titlePhase='prepared';observe('animation-after',state);return state.titleAnimation;
  }
  static startTitleAnimation(state){
    if(state.titlePhase!=='prepared')throw new Error("Title animation is not ready");
    // Main 4444 restores the normal pointer before entering the script loop.
    this.selectCursor(state,0);state.titlePhase='playing';
  }
  static finishTitleAnimation(state,querySound){
    if(state.titlePhase!=='playing')throw new Error("Title animation is not playing");
    // Main 4A56 calls E5A2, a playback-status query with a source-load side
    // effect. It does not start this sound or replace the active title music.
    const queried=this.loadSound(state,querySound);if(queried)state.memory.address(queried);
    state.titleAnimation.dispose();state.direct.release(state.titleScript);
    state.titleScript=0;state.titlePhase='finished';
  }
  static releaseTitle(state){
    if(state.titlePhase!=='finished')throw new Error("Title animation must finish before title release");
    const m=state.memory;m.freeHandle(state.titlePalette);state.titlePalette=0;
    m.freeRaw(state.titleSurface.pixels);m.near.free(state.titleSurface.rows);
    state.titleSurface=null;state.titlePhase='released';
  }
  static finishTitleMusic(state){
    // The audio-completion/stop callback releases the active resource lock.
    // Overlay 5:3C2 waits for this completion before proceeding to the room
    // setup; its timing remains the audio player's responsibility.
    if(state.titleSound){state.memory.unlock(state.titleSound);state.titleSound=0;}
  }
  static prepareEntrance(state,{palettes,screenBounds,childPalettes,savedBounds,script},observe=()=>{}){
    // Main 547..5A4 and ACE..C0B, for the initial child-selection screen.
    // Palette IDs/banks and rectangles come from the original program.
    const m=state.memory,loader=new OriginalPaletteLoading(state.catalogs);
    state.interfacePalettes=new Map();
    for(const config of palettes){
      state.interfacePalettes.set(config.id,loader.load(config.id,config.banks));
      observe(`interface-palette-${config.id}`,state);
    }
    this.selectCursor(state,1);m.heap.pack(0xffffff);
    const background=state.interfacePalettes.get(palettes[0].id),decoration=state.interfacePalettes.get(palettes[1].id);
    m.address(background);
    const [top,left,bottom,right]=screenBounds;
    state.entranceSurface={rows:m.near.allocate(2*(bottom-top)),pixels:m.allocateRaw((bottom-top)*(right-left)),bounds:[...screenBounds]};
    const draw=(palette,relative)=>m.freeHandle(this.loadShape(state,palette,relative));
    draw(background,1);
    // Overlay 5:74 draws the clock backing and its initial decoration.
    draw(background,2);draw(decoration,4);draw(background,3);
    state.childPalettes=[];
    for(const config of childPalettes){
      state.childPalettes.push(loader.load(config.id,config.banks));
      observe(`child-palette-${config.id}`,state);
    }
    // 59C0 uploads the second child's colors through an existing palette.
    m.address(state.childPalettes[1]);
    state.entranceSaved=savedBounds.map(bounds=>new OriginalSavedSurface(m,{bounds,pixelsPerByte:1}));
    return this.prepareEntranceFrame(state,{id:childPalettes[0].id,palette:state.childPalettes[0],script},observe);
  }
  static prepareEntranceFrame(state,{id,palette,script},observe=()=>{}){
    if(state.entranceAnimation&&!state.entranceAnimation.disposed)throw new Error("Entrance animation is still owned");
    const m=state.memory;
    this.selectCursor(state,1);
    const found=state.catalogs.resolve('SCR',id);
    if(!found)throw new Error("Missing entrance script");
    state.entranceScript=state.direct.load({payload:found.entry.payload,catalogHandle:found.catalog.handle,cachedHandle:found.entry.handle});
    const data=m.resourcePayloads.get(palette);m.address(palette);
    observe('entrance-animation-before',state);
    state.entranceAnimation=OriginalAnimationMemory.prepare(m,{script,last:data[2]|data[3]<<8,paletteHandle:palette,loadShape:relative=>this.loadShape(state,palette,relative)});
    state.entrancePhase='prepared';observe('entrance-animation-after',state);return state.entranceAnimation;
  }
  static finishEntranceFrame(state,querySound){
    if(state.entrancePhase!=='prepared')throw new Error("Entrance frame is not prepared");
    // Main C0B/C3F/C6B ask the wrapper to return after the first display.
    // The normal cursor is selected before display; 4A56 then queries sound.
    this.selectCursor(state,0);
    const queried=this.loadSound(state,querySound);if(queried)state.memory.address(queried);
    state.entranceAnimation.dispose();state.direct.release(state.entranceScript);
    state.entranceScript=0;state.entrancePhase='finished';
  }
  static finishEntrance(state,music){
    if(state.entrancePhase!=='finished')throw new Error("Entrance frame must finish first");
    const m=state.memory;
    m.freeRaw(state.entranceSurface.pixels);m.near.free(state.entranceSurface.rows);state.entranceSurface=null;
    state.entranceMusic=this.loadSound(state,music);m.lock(state.entranceMusic);
    this.selectCursor(state,0);state.entrancePhase='ready';
  }
  static initializeEntrance(state,config,observe=()=>{}){
    // Main BCF..D0E retains the lower backgrounds, saves the other child's
    // pose between previews, then transfers the completed screen and starts
    // background music. The renderer may draw at each animation-after hook.
    const m=state.memory;
    this.prepareEntrance(state,config,observe);this.finishEntranceFrame(state,config.querySound);
    state.girlEntranceSaved=new OriginalSavedSurface(m,{bounds:config.postPreviewBounds[0]});
    state.entranceSaved[2].dispose();
    this.prepareEntranceFrame(state,{id:config.childPalettes[1].id,palette:state.childPalettes[1],script:config.scripts[1]},
      (stage,s)=>observe(stage.replace('entrance-animation-','entrance-animation-2-'),s));
    this.finishEntranceFrame(state,config.querySound);
    state.boyEntranceSaved=new OriginalSavedSurface(m,{bounds:config.postPreviewBounds[1]});
    this.prepareEntranceFrame(state,{id:config.childPalettes[0].id,palette:state.childPalettes[0],script:config.scripts[0]},
      (stage,s)=>observe(stage.replace('entrance-animation-','entrance-animation-3-'),s));
    this.finishEntranceFrame(state,config.querySound);this.finishEntrance(state,config.music);
    observe('entrance-ready',state);
  }
  static selectEntrance(state,{sex,childPalettes,scripts,querySound},observe=()=>{}){
    if(state.entrancePhase!=='ready'||![0,1].includes(sex))throw new Error("Entrance selection is not ready");
    const m=state.memory,upper=[state.boyEntranceSaved,state.girlEntranceSaved];
    // Main 0805..092B runs the chosen child's departure, the other child's
    // departure, then the chosen child's climb. Each caller-owned saved
    // background is released only after the corresponding script returns.
    const play=(child,scriptIndex,number)=>{
      this.prepareEntranceFrame(state,{id:childPalettes[0].id+scriptIndex,palette:state.childPalettes[child],script:scripts[scriptIndex]},
        (label,s)=>observe(label.replace('entrance-animation-',`selection-animation-${number}-`),s));
      this.finishEntranceFrame(state,querySound);
    };
    play(sex,sex,1);upper[sex].dispose();
    play(1-sex,1-sex,2);upper[1-sex].dispose();state.entranceSaved[1-sex].dispose();
    play(sex,sex+2,3);state.entranceSaved[sex].dispose();
    for(const palette of state.childPalettes)m.freeHandle(palette);
    state.childPalettes=[];state.entrancePhase='selected';state.selectedChild=sex;
    observe('selection-complete',state);
  }
  static prepareEntranceIdle(state,cloud){
    if(state.entrancePhase!=='ready')throw new Error("Entrance is not ready");
    // Main 05B6 queries the initial cloud dimensions after entrance setup.
    state.memory.freeHandle(this.loadShape(state,state.interfacePalettes.get(170),cloud+1));
  }
  static advanceEntranceCredit(state,bounds){
    if(state.entrancePhase!=='ready')throw new Error("Entrance is not ready");
    const m=state.memory,[top,left,bottom,right]=bounds;
    // Overlay 5:74 creates a temporary drawing surface for each credit change.
    const rows=m.near.allocate(2*(bottom-top)),pixels=m.allocateRaw((bottom-top)*(right-left));
    m.freeHandle(this.loadShape(state,state.interfacePalettes.get(0),2));
    state.entranceCredit=((state.entranceCredit||0)+1)%8;
    m.freeHandle(this.loadShape(state,state.interfacePalettes.get(6),state.entranceCredit+4));
    m.freeRaw(pixels);m.near.free(rows);
  }
  static openSelectedChild(state,archive){
    if(state.entrancePhase!=='selected')throw new Error("Child selection has not completed");
    if(state.entranceMusic){state.memory.unlock(state.entranceMusic);state.entranceMusic=0;}
    const files=state.catalogs.files;
    state.childCatalog=state.catalogs.open({...archive,volume:files[0].volume,fileHandle:1+Math.max(...files.map(f=>f.fileHandle))});
    state.entrancePhase='child-open';
  }
  static prepareRoom(state,config,observe=()=>{}){
    if(state.entrancePhase!=='child-open')throw new Error("Selected child archive is not open");
    const m=state.memory,c=state.catalogs,loader=new OriginalPaletteLoading(c);
    this.selectCursor(state,1);m.heap.pack(0xffffff);
    // Main 77D3 restores the VGA base colors from the ordinary resource table.
    const colors=c.resolve('',10);
    if(!colors)throw new Error("Missing VGA base colors");
    const colorSource=c.loadSource(colors.catalog.handle,'',10);m.address(colorSource);m.discardable(colorSource);
    for(const id of [870,900,930,170,6])m.address(state.interfacePalettes.get(id));
    const [top,left,bottom,right]=config.screenBounds;
    state.roomSurface={rows:m.near.allocate(2*(bottom-top)),pixels:m.allocateRaw((bottom-top)*(right-left))};
    state.roomPalettes=new Map();
    for(const palette of config.palettes){
      state.roomPalettes.set(palette.id,loader.load(palette.id,palette.banks));
      observe(`room-palette-${palette.id}`,state);
    }
    const palette=id=>state.roomPalettes.get(id)||state.interfacePalettes.get(id);
    const draw=(id,relative)=>m.freeHandle(this.loadShape(state,palette(id),relative));
    draw(4,1);m.discardable(state.roomPalettes.get(4));state.roomPalettes.delete(4);
    draw(900,26);draw(900,19);draw(1200,1);draw(1200,28);
    // The date formatter loads the month-name table; lettering itself uses
    // the already active font. Chalk-tool fills do not create resources.
    const months=c.resolve('STRL',500),monthSource=c.loadSource(months.catalog.handle,'STRL',500);
    m.address(monthSource);m.discardable(monthSource);
    state.theaterSaved=new OriginalSavedSurface(m,{bounds:config.theaterBounds});
    draw(1100,9);draw(1250,6);draw(1250,1);
    // 22E1 retains the converted cloud through the calendar overlay draw,
    // then releases it at 23D7. Releasing it first changes later placement.
    const cloud=this.loadShape(state,palette(170),config.cloud+1);m.address(cloud);
    draw(1200,1);m.freeHandle(cloud);
    const hour=config.hour%12||12;
    draw(1200,hour>9?27:26);draw(1200,hour%10+15);draw(1200,25);
    draw(1200,Math.floor(config.minute/10)+15);draw(1200,config.minute%10+15);
    state.roomObjects=config.objects.map(o=>({...o,bounds:[...o.bounds],saved:null}));
    const drawObjects=(objects=state.roomObjects)=>{for(const o of objects){
      o.saved=new OriginalSavedSurface(m,{bounds:o.bounds});draw(o.palette,o.relative);
    }};
    observe('room-objects-before',state);
    drawObjects();
    observe('room-objects-after',state);
    // Main 39BF temporarily restores objects in front of the character.
    // Calendar drawing clears its top-edge selection mode on return (340A).
    // AD72 therefore selects by bottom edge here, and always includes balloons.
    const foreground=state.roomObjects.filter(o=>o.type===6||o.bounds[2]>=config.characterBounds[2]);
    for(const o of [...foreground].reverse())o.saved.dispose();
    state.characterSaved=new OriginalSavedSurface(m,{bounds:config.characterBounds});draw(20500,1);
    drawObjects(foreground);
    // Main 35FA restores and redraws objects around the empty alarm-time panel.
    for(const o of [...state.roomObjects].reverse())o.saved.dispose();
    drawObjects();
    m.freeRaw(state.roomSurface.pixels);m.near.free(state.roomSurface.rows);state.roomSurface=null;
    this.selectCursor(state,0);state.entrancePhase='room';observe('room-complete',state);
  }
  static beginRoomTransfer(state,{palette,sound,script},observe=()=>{}){
    if(state.entrancePhase!=='room')throw new Error("Room transfer requires a prepared room");
    const m=state.memory,c=state.catalogs;
    // Main 5204 opens the ring group and starts its independently looping
    // sound before entering the common animation wrapper (415F/419D).
    state.transferPalette=new OriginalPaletteLoading(c).load(palette.id,palette.banks);
    state.transferSound=this.loadSound(state,sound);m.lock(state.transferSound);
    this.selectCursor(state,1);
    const found=c.resolve('SCR',palette.id);
    if(!found)throw new Error("Missing room transfer script");
    state.transferScript=state.direct.load({payload:found.entry.payload,catalogHandle:found.catalog.handle,cachedHandle:found.entry.handle});
    const data=m.resourcePayloads.get(state.transferPalette);m.address(state.transferPalette);
    observe('transfer-animation-before',state);
    state.transferAnimation=OriginalAnimationMemory.prepare(m,{script,last:data[2]|data[3]<<8,paletteHandle:state.transferPalette,
      loadShape:relative=>this.loadShape(state,state.transferPalette,relative),
      // C9ED draws the standing child over the initial ring background.
      // The default room objects do not intersect this script rectangle.
      composeInitial:()=>m.freeHandle(this.loadShape(state,state.roomPalettes.get(20500),1))});
    state.entrancePhase='transfer-prepared';observe('transfer-animation-after',state);
    return state.transferAnimation;
  }
  static startRoomRing(state){
    if(state.entrancePhase!=='transfer-prepared')throw new Error("Room ring is not prepared");
    this.selectCursor(state,0);state.entrancePhase='ring-playing';
  }
  static composeRoomRing(state){
    if(state.entrancePhase!=='ring-playing')throw new Error("Room ring is not playing");
    // C9ED/CA96 calls 39BF without saving/restoring backgrounds on each
    // composition. The initial central-room objects do not intersect it.
    state.memory.freeHandle(this.loadShape(state,state.roomPalettes.get(20500),1));
  }
  static prepareBoardBubble(state,{querySound,inletBounds,id,script},observe=()=>{}){
    if(state.entrancePhase!=='ring-playing')throw new Error("Room ring is not playing");
    const m=state.memory,c=state.catalogs;
    const queried=this.loadSound(state,querySound);if(queried)m.address(queried);
    // Base 980 bypasses sound stop: its loop survives until the bubble sound.
    state.transferAnimation.dispose();state.direct.release(state.transferScript);state.transferScript=0;
    const temporary=bounds=>{
      const [top,left,bottom,right]=bounds;
      return {rows:m.near.allocate(2*(bottom-top)),pixels:m.allocateRaw((bottom-top)*(right-left))};
    };
    const release=surface=>{m.freeRaw(surface.pixels);m.near.free(surface.rows);};
    const draw=(palette,relative)=>m.freeHandle(this.loadShape(state,palette,relative));
    // Main 526C: 39BF(1,1,1,1,0,0) redraws the ring and replaces the
    // character backing inside a temporary surface before drawing the child.
    const bounds=[...state.characterSaved.bounds],surface=temporary(bounds);
    state.characterSaved.dispose();draw(state.transferPalette,6);
    state.characterSaved=new OriginalSavedSurface(m,{bounds});
    draw(state.roomPalettes.get(20500),1);release(surface);
    m.discardable(state.transferPalette);state.transferPalette=0;
    // Main 61FF saves the board inlet while its temporary surface is owned.
    const inlet=temporary(inletBounds);
    state.inletSaved=new OriginalSavedSurface(m,{bounds:inletBounds});
    draw(state.interfacePalettes.get(900),27);release(inlet);
    this.selectCursor(state,1);
    const found=c.resolve('SCR',id);if(!found)throw new Error("Missing board bubble script");
    state.transferScript=state.direct.load({payload:found.entry.payload,catalogHandle:found.catalog.handle,cachedHandle:found.entry.handle});
    // Main 4338..43A7 prepares the authored PSL sounds before constructing
    // the animation. The list is released; the prepared sounds stay cached.
    const list=c.resolve('PSL',id);if(!list)throw new Error("Missing board bubble sound list");
    const listHandle=c.loadSource(list.catalog.handle,'PSL',id),sounds=m.resourcePayloads.get(listHandle);
    m.address(listHandle);
    const count=sounds[0]|sounds[1]<<8;
    if(sounds.length!==2+count*2)throw new Error("Malformed board bubble sound list");
    for(let i=0;i<count;i++){m.address(listHandle);this.loadSound(state,sounds[2+2*i]|sounds[3+2*i]<<8);}
    m.freeHandle(listHandle);
    const palette=state.roomPalettes.get(1100),data=m.resourcePayloads.get(palette);m.address(palette);
    observe('bubble-animation-before',state);
    state.transferAnimation=OriginalAnimationMemory.prepare(m,{script,last:data[2]|data[3]<<8,paletteHandle:palette,
      loadShape:relative=>this.loadShape(state,palette,relative)});
    state.entrancePhase='bubble-prepared';observe('bubble-animation-after',state);
    return state.transferAnimation;
  }
  static startBoardBubble(state){
    if(state.entrancePhase!=='bubble-prepared')throw new Error("Board bubble is not prepared");
    this.selectCursor(state,0);state.entrancePhase='bubble-playing';
  }
  static playBoardBubbleSound(state,id){
    if(state.entrancePhase!=='bubble-playing')throw new Error("Board bubble is not playing");
    const sound=this.loadSound(state,id);
    if(state.transferSound)state.memory.unlock(state.transferSound);
    state.transferSound=sound;state.memory.lock(sound);
  }
  static finishRoomTransfer(state,querySound,observe=()=>{}){
    if(state.entrancePhase!=='bubble-playing')throw new Error("Board bubble is not playing");
    const m=state.memory;
    const queried=this.loadSound(state,querySound);if(queried)m.address(queried);
    // Caller reaches this semantic boundary after the sound-tail wait/stop.
    // The renderer restores the bubble backing without new allocations.
    if(state.transferSound)m.unlock(state.transferSound);state.transferSound=0;
    state.transferAnimation.dispose();state.direct.release(state.transferScript);state.transferScript=0;
    // Main 61FF(0) restores and frees the inlet on a temporary surface.
    const [top,left,bottom,right]=state.inletSaved.bounds;
    const rows=m.near.allocate(2*(bottom-top)),pixels=m.allocateRaw((bottom-top)*(right-left));
    state.inletSaved.dispose();state.inletSaved=null;
    m.freeRaw(pixels);m.near.free(rows);
    state.entrancePhase='transfer-complete';observe('transfer-complete',state);
  }
  static releaseRoom(state,observe=()=>{}){
    if(state.entrancePhase!=='transfer-complete')throw new Error("Room transfer must complete before room release");
    const m=state.memory;
    observe('room-release-before',state);
    // Main 3217/8E54 releases current-scene object backgrounds in list order,
    // then the theater and child backgrounds. This path has no alarm backing.
    for(const object of state.roomObjects)object.saved.dispose();
    state.theaterSaved.dispose();state.characterSaved.dispose();
    for(const id of [20500,1200,1250,1100])m.discardable(state.roomPalettes.get(id));
    state.roomPalettes.clear();m.heap.pack(0xffffff);
    state.entrancePhase='room-released';observe('room-release-after',state);
  }
}
