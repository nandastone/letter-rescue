"""Compare generated cold-boot ownership through the three title animations."""
from pathlib import Path
import argparse,base64,hashlib,json,struct,time,zipfile
from playwright.sync_api import sync_playwright
from executable import unpack,disassemble_script
from resources import parse_archive
from verify_startup_activation import resource_inputs
from verify_resource_growth import ROOT,DATA,digest,arena_state
from verify_near_heap import parse as parse_near
from verify_dos_resource_startup import mcbs
from memory_catalog import read_files,read_catalogs


def verify(output,entrance=False,selection=None,room=False,transfer=False,board=False):
    started=time.perf_counter()
    transfer=transfer or board
    room=room or transfer
    if transfer and selection=='girl':raise ValueError('Transfer reference currently covers boy startup')
    selection=selection or ('boy' if room else None)
    entrance=entrance or selection is not None
    output.mkdir(parents=True,exist_ok=False);inputs=resource_inputs()
    with zipfile.ZipFile(DATA/'source/The_Treehouse_1991.zip') as z:
        image,info=unpack(z.read('TheTreeh/treehse.exe'));exe=z.read('TheTreeh/treehse.exe')
        overlay=next(o for o in info['overlays'] if o['id']==5)
        code=exe[overlay['file_offset']+overlay['header_bytes']:overlay['file_offset']+overlay['size']]
        word=lambda offset:struct.unpack_from('<H',code,offset)[0]
        assert code[0x20f]==code[0x213]==code[0x287]==code[0x28b]==code[0x297]==0xb8
        background=dict(id=word(0x210),banks=word(0x214));animation=dict(id=word(0x288),banks=word(0x28c))
        data=z.read('TheTreeh/th.dat');entry=next(r for r in parse_archive(data) if r['tag']=='SCR' and r['id']==animation['id'])
        script=disassemble_script(data[entry['payload_offset']:entry['payload_offset']+entry['size']],image)
        assert code[0x2b2:0x2b5]==bytes.fromhex('837ec6') and image[0x4a56]==0xb8
        count=code[0x2b5]
        origins=[list(reversed(struct.unpack_from('<2h',image,0x321d0+0x14c0+4*i))) for i in range(count)]
        x,y=origins[0]
        title=dict(backgroundPalette=background,animationPalette=animation,sound=word(0x298),
            backgroundBounds=list(struct.unpack_from('<4h',image,0x321d0+0x14b8)),animationOrigin=[x,y],
            animationOrigins=origins,querySound=struct.unpack_from('<H',image,0x4a57)[0],
            script=dict(bounds=script['bounds_words'],code=[[op['opcode'],list(bytes.fromhex(op['operand_hex']))] for op in script['instructions']]))
        palette_config=lambda offset:dict(id=struct.unpack_from('<H',image,offset+1)[0],banks=struct.unpack_from('<H',image,offset+5)[0])
        ui=[palette_config(0x547+16*i) for i in range(6)];children=[palette_config(at) for at in [0xb9b,0xbab]]
        child_scripts=[]
        for child in children+[dict(id=children[0]['id']+i) for i in [2,3]]:
            entry=next(r for r in parse_archive(data) if r['tag']=='SCR' and r['id']==child['id'])
            child_script=disassemble_script(data[entry['payload_offset']:entry['payload_offset']+entry['size']],image)
            child_scripts.append(dict(bounds=child_script['bounds_words'],code=[[op['opcode'],list(bytes.fromhex(op['operand_hex']))] for op in child_script['instructions']]))
        saved_offsets=[struct.unpack_from('<H',image,at)[0] for at in [0xbc9,0xbd6,0xbe3]]
        entrance_config=dict(palettes=ui,childPalettes=children,screenBounds=list(struct.unpack_from('<4h',image,0x321d0+0x15f8)),
            savedBounds=[list(struct.unpack_from('<4h',image,0x321d0+at)) for at in saved_offsets],
            postPreviewBounds=[list(struct.unpack_from('<4h',image,0x321d0+struct.unpack_from('<H',image,at)[0])) for at in [0xc0f,0xc43]],
            music=struct.unpack_from('<H',image,0xcfd)[0],querySound=title['querySound'],script=child_scripts[0],scripts=child_scripts,
            creditBounds=list(struct.unpack_from('<4h',image,0x321d0+0x142c)))
        room_config={}
        transfer_config={}
        board_config={}
        if board:
            overlay3=next(o for o in info['overlays'] if o['id']==3)
            board_code=exe[overlay3['file_offset']+overlay3['header_bytes']:overlay3['file_offset']+overlay3['size']]
            board_palettes=[]
            for at in range(0x20,0x80,0x10):
                assert board_code[at]==board_code[at+4]==0xb8
                board_palettes.append(dict(id=struct.unpack_from('<H',board_code,at+1)[0],banks=struct.unpack_from('<H',board_code,at+5)[0]))
            assert board_code[0x693]==0x05 and board_code[0x6a5]==0xb8
            tables=json.loads((ROOT/'treehouse-demo/boardgame-tables.json').read_text(encoding='utf-8'))
            game_rects=tables['game_rects'][:6]+tables['money_rects']
            board_config=dict(palettes=board_palettes,screenBounds=entrance_config['screenBounds'],
                backgroundPalette=dict(id=10*struct.unpack_from('<H',board_code,0x694)[0],banks=struct.unpack_from('<H',board_code,0x6a6)[0]),
                optionsPalette=dict(id=struct.unpack_from('<H',board_code,0xb1f)[0],banks=struct.unpack_from('<H',board_code,0xb23)[0]),gameRects=game_rects,optionsRects=tables['options_rects'])
        if room:
            ds=0x321d0;sex=selection=='girl'
            filename_offset=struct.unpack_from('<H',image,ds+0x248+2*sex)[0]
            filename=image[ds+filename_offset:].split(b'\0',1)[0].decode('ascii')
            member=next(n for n in z.namelist() if n.lower()=='thetreeh/'+filename.lower())
            child_archive=dict(archive=list(z.read(member)),filename='C:\\THETREEH\\'+filename)
            character_bounds=list(struct.unpack_from('<4h',image,ds+0x1c4))
            if not sex:character_bounds[0]+=4
            room_config=dict(palettes=[palette_config(at) for at in [0x1ff1,0x2001,0x2011,0x2021,0x2031]],
                screenBounds=entrance_config['screenBounds'],theaterBounds=list(struct.unpack_from('<4h',image,0x2e8f0+0x48+0x68)),
                characterBounds=character_bounds,cloud=5,hour=12,minute=0,
                objects=[dict(type=i,palette=[870,900,930][struct.unpack_from('<H',image,ds+0x5f6+2*i)[0]],
                    relative=struct.unpack_from('<H',image,ds+0x936+10*i+2)[0],bounds=list(struct.unpack_from('<4h',image,ds+0x7be+8*i))) for i in [9,20,8,10,6]],
                archive=child_archive)
        if transfer:
            group=palette_config(0x5217)
            entry=next(r for r in parse_archive(data) if r['tag']=='SCR' and r['id']==group['id'])
            ring=disassemble_script(data[entry['payload_offset']:entry['payload_offset']+entry['size']],image)
            transfer_config=dict(palette=group,sound=struct.unpack_from('<H',image,0x5234)[0],
                script=dict(bounds=ring['bounds_words'],code=[[op['opcode'],list(bytes.fromhex(op['operand_hex']))] for op in ring['instructions']]))
            entry=next(r for r in parse_archive(data) if r['tag']=='SCR' and r['id']==1103)
            bubble=disassemble_script(data[entry['payload_offset']:entry['payload_offset']+entry['size']],image)
            transfer_config['bubble']=dict(id=1103,querySound=title['querySound'],
                inletBounds=list(struct.unpack_from('<4h',image,0x321d0+0x3d6)),
                script=dict(bounds=bubble['bounds_words'],code=[[op['opcode'],list(bytes.fromhex(op['operand_hex']))] for op in bubble['instructions']]))
    references={};fixtures={}
    boundaries=[('background-palette','resource-startup-palette-a',1),('title-palette','resource-startup-palette-a',3),
                                ('animation-before','resource-startup-animation-a',0),('animation-after','resource-startup-animation-a',1),
                                ('animation-2-before','resource-startup-animation-a',2),('animation-2-after','resource-startup-animation-a',3),
                                ('animation-3-before','resource-startup-animation-a',4),('animation-3-after','resource-startup-animation-a',5),
                                ('title-complete','resource-startup-palette-a',4)]
    if entrance:
        boundaries.extend((f"interface-palette-{c['id']}",'resource-startup-palette-a',5+2*i) for i,c in enumerate(ui))
        boundaries.extend((f"child-palette-{c['id']}",'resource-startup-palette-a',17+2*i) for i,c in enumerate(children))
        boundaries.extend([('entrance-animation-before','resource-startup-animation-a',6),('entrance-animation-after','resource-startup-animation-a',7)])
        boundaries.extend([('entrance-animation-2-before','resource-startup-animation-a',8),('entrance-animation-2-after','resource-startup-animation-a',9),
                           ('entrance-animation-3-before','resource-startup-animation-a',10),('entrance-animation-3-after','resource-startup-animation-a',11),
                           ('entrance-ready','resource-startup-entrance-a',1)])
    if selection:
        boundaries.append(('selection-before',f'resource-selection-{selection}-a',0))
        for i in range(3):
            boundaries.extend([(f'selection-animation-{i+1}-before',f'resource-selection-animation-{selection}-a',12+2*i),
                               (f'selection-animation-{i+1}-after',f'resource-selection-animation-{selection}-a',13+2*i)])
        boundaries.append(('selection-complete',f'resource-selection-{selection}-a',1))
    if room:
        boundaries.extend([('room-before',f'resource-room-{selection}-a',0),('room-complete',f'resource-room-{selection}-a',1)])
        if selection=='boy':boundaries.extend((f"room-palette-{p['id']}",'resource-room-palette-boy-a',21+2*i) for i,p in enumerate(room_config['palettes']))
        if selection=='boy':boundaries.extend([('room-objects-before','resource-room-objects-boy-a',0),('room-objects-after','resource-room-objects-boy-a',1)])
    if transfer:
        boundaries.extend([('transfer-before','resource-room-board-transfer-a',0),
            ('transfer-animation-before','resource-room-board-animation-a',18),('transfer-animation-after','resource-room-board-animation-a',19),
            ('bubble-animation-before','resource-room-board-animation-a',20),('bubble-animation-after','resource-room-board-animation-a',21),
            ('transfer-complete','resource-room-board-transfer-a',1),
            ('room-release-before','resource-room-board-release-a',0),('room-release-after','resource-room-board-release-a',1)])
    if board:
        boundaries.append(('board-before','resource-board-start-palette-a',32))
        boundaries.extend((f"board-palette-{p['id']}",'resource-board-start-palette-a',33+2*i) for i,p in enumerate(board_config['palettes']))
        boundaries.extend([('board-background-before','resource-board-start-palette-a',44),('board-background-after','resource-board-start-palette-a',45)])
        boundaries.extend([('board-options-before','resource-board-start-palette-a',46),('board-options-after','resource-board-start-palette-a',47)])
        boundaries.append(('board-options-painted','resource-board-options-a',1))
    for label,folder,index in boundaries:
        path=DATA/folder;run=json.loads((path/'run.json').read_text());assert run['passed'] and run['fixed_clock']
        references[folder]=digest(path/'run.json');f=run['heap'][index];raw=(path/f['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==f['sha256']
        arena=arena_state(raw,f['ss'])[0];payloads={b['handle']:b.pop('payload') for b in arena['heap']['blocks'] if 'payload' in b}
        fixtures[label]=dict(arena=arena,near=parse_near(raw,f['ss']),dos=mcbs(raw),files=read_files(raw,f['ss']),catalogs=read_catalogs(raw,f['ss']),payloads=payloads)
        if board and label=='board-before':board_config['entrySeed']=struct.unpack_from('<I',raw,f['ss']*16+0x5290)[0]
        if board and label=='board-options-before':
            ds=f['ss']*16
            board_config['expectedGame']=dict(seed=struct.unpack_from('<I',raw,ds+0x5290)[0],nodes=list(struct.unpack_from('<2h',raw,ds+0x52c4)),
                directions=list(struct.unpack_from('<2h',raw,ds+0x5734)),balances=list(struct.unpack_from('<2h',raw,ds+0x5a0c)),types=list(struct.unpack_from('<24h',raw,ds+0x59da)))
    # Transport archive bytes compactly; Playwright otherwise creates one
    # protocol object per byte. The resource model receives identical bytes.
    for archive in inputs['archives']:archive['archive']=base64.b64encode(bytes(archive['archive'])).decode('ascii')
    if room:room_config['archive']['archive']=base64.b64encode(bytes(room_config['archive']['archive'])).decode('ascii')
    modules=['engine.js','heap.js','near-heap.js','memory.js','dos-memory.js','resource-startup.js','resource-loading.js','font-loading.js','cursor-loading.js','saved-surface.js','catalog-loading.js','direct-loading.js','sound-loading.js','shape-loading.js','palette-loading.js','animation-memory.js','startup-resources.js']
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in modules:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        if board:
            for name in ['board-resources.js','board-motion.js','boardgame.js']:
                modules.append(name);page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        result=page.evaluate('''a=>{
          const stages={},focused=[];let error=null,state;
          const encodePayload=data=>{
            let binary='';for(let i=0;i<data.length;i+=16384)binary+=String.fromCharCode(...data.slice(i,i+16384));
            return btoa(binary);
          };
          const observe=(label,s)=>{
            const heap=s.memory.heap.snapshot();heap.blocks=heap.blocks.map(({payload,...b})=>b);
            stages[label]=structuredClone({arena:{...s.memory.arena,heap},near:s.memory.near.snapshot(),dos:s.dos.snapshot(),
              files:s.catalogs.files,catalogs:s.catalogs.files.map(f=>s.catalogs.snapshot(f.handle)),
              payloads:Array.from(s.memory.resourcePayloads,([id,data])=>[id,encodePayload(data)])});
          };
          try{
            for(const archive of a.inputs.archives)archive.archive=bytes(archive.archive);
            if(a.room)a.roomConfig.archive.archive=bytes(a.roomConfig.archive.archive);
            state=OriginalStartupResources.create(a.inputs);OriginalStartupResources.prepareTitle(state,a.title,observe);
            for(let i=0;i<a.title.animationOrigins.length;i++){
              if(i)OriginalStartupResources.prepareTitleAnimation(state,{id:a.title.animationPalette.id,script:a.title.script,origin:a.title.animationOrigins[i]},
                (stage,s)=>observe(stage.replace('animation-',`animation-${i+1}-`),s));
              OriginalStartupResources.startTitleAnimation(state);
              OriginalStartupResources.finishTitleAnimation(state,a.title.querySound);
            }
            OriginalStartupResources.releaseTitle(state);
            // Overlay 5 waits for the title sound before leaving. This check
            // advances to semantic completion; it does not assert audio time.
            OriginalStartupResources.finishTitleMusic(state);observe('title-complete',state);
            if(a.entrance)OriginalStartupResources.initializeEntrance(state,a.entranceConfig,observe);
            if(a.selection){
              // Replay the two visible credit changes in this ordinary-input
              // recording. These are semantic renderer events, not allocator
              // requests. Joining their live timer remains separate work.
              OriginalStartupResources.prepareEntranceIdle(state,5);
              for(let i=0;i<2;i++)OriginalStartupResources.advanceEntranceCredit(state,a.entranceConfig.creditBounds);
              observe('selection-before',state);
              OriginalStartupResources.selectEntrance(state,{...a.entranceConfig,sex:a.selection==='girl'?1:0},observe);
              focused.push({name:'selection releases all four child backgrounds and both palettes',passed:
                state.entrancePhase==='selected'&&!state.childPalettes.length&&!state.boyEntranceSaved.descriptor&&!state.girlEntranceSaved.descriptor&&state.entranceSaved.slice(0,2).every(s=>!s.descriptor)});
              let rejected=false;try{OriginalStartupResources.selectEntrance(state,{...a.entranceConfig,sex:0});}catch(e){rejected=true;}
              focused.push({name:'completed selection cannot dispose its resources twice',passed:rejected});
            }
            if(a.room){
              OriginalStartupResources.openSelectedChild(state,a.roomConfig.archive);
              observe('room-before',state);
              OriginalStartupResources.prepareRoom(state,a.roomConfig,observe);
            }
            if(a.transfer){
              observe('transfer-before',state);
              OriginalStartupResources.beginRoomTransfer(state,a.transferConfig,observe);
              const ring=a.transferConfig.script;
              if(ring.code.some(([op])=>op===7))throw new Error('Ring now needs an offscreen composition hook');
              const store={data:{scripts:{'TH:980':ring}},prepareAnimation:()=>state.transferAnimation};
              OriginalStartupResources.startRoomRing(state);
              const playback=new Animation(store,'TH',980,980,{onDisplay:()=>OriginalStartupResources.composeRoomRing(state)});
              for(let tick=0;!playback.done&&tick<10000;tick++)playback.update(tick);
              focused.push({name:'original ring script reaches completion through the shared animation interpreter',passed:playback.done&&playback.frameUpdates===18});
              OriginalStartupResources.prepareBoardBubble(state,a.transferConfig.bubble,observe);
              const bubble=a.transferConfig.bubble.script,callbacks=[],sounds=[];
              OriginalStartupResources.startBoardBubble(state);
              const bubbleStore={data:{scripts:{'TH:1103':bubble}},prepareAnimation:()=>state.transferAnimation};
              const bubblePlayback=new Animation(bubbleStore,'TH',1103,1100,{
                onSound:id=>{sounds.push(id);OriginalStartupResources.playBoardBubbleSound(state,id);},
                // Callback 0 restores the saved child pixels without releasing
                // their owner. No default room object intersects this bubble.
                onCallback:(slot,operand)=>callbacks.push([slot,operand])});
              for(let tick=0;!bubblePlayback.done&&tick<10000;tick++)bubblePlayback.update(tick);
              focused.push({name:'original board bubble completes with its authored sounds and removal callback',passed:
                bubblePlayback.done&&bubblePlayback.frameUpdates===13&&JSON.stringify(sounds)==='[10034,10035]'&&JSON.stringify(callbacks)==='[[0,0]]'});
              OriginalStartupResources.finishRoomTransfer(state,a.transferConfig.bubble.querySound,observe);
              focused.push({name:'finished room transfer releases animation, script, inlet and playing sound',passed:
                state.transferAnimation.disposed&&!state.transferScript&&!state.inletSaved&&!state.transferSound});
              OriginalStartupResources.releaseRoom(state,observe);
              focused.push({name:'room release disposes each saved background and releases palette ownership',passed:
                !state.roomPalettes.size&&!state.theaterSaved.descriptor&&!state.characterSaved.descriptor&&state.roomObjects.every(o=>!o.saved.descriptor)});
            }
            if(a.board){
              OriginalBoardResources.prepare(state,a.boardConfig,observe);
              const game=new BoardGame({data:{boardgame:a.boardTables}});game.seed=a.boardConfig.entrySeed;game.enter();
              OriginalBoardResources.beginDrawing(state,a.boardConfig,observe);
              OriginalBoardResources.prepareOptions(state,a.boardConfig,game,observe);
              focused.push({name:'existing board gameplay generates the original entry state from one entry seed',passed:
                Object.entries(a.boardConfig.expectedGame).every(([key,value])=>JSON.stringify(game[key])===JSON.stringify(value))});
              OriginalBoardResources.finishOptions(state,a.boardConfig,game,observe);
              focused.push({name:'initial board and options temporary screens are released at ready state',passed:
                state.entrancePhase==='board-options-ready'&&!state.boardSurface&&!state.boardOptionsSurface});
            }
            const m=state.memory,c=state.catalogs,palettes=new OriginalPaletteLoading(c),id=a.title.backgroundPalette.id;
            const found=c.resolve('SHPL',id),key='SHPL:'+id;
            focused.push({name:'released title-background palette clears its catalog and cache entries',passed:found.entry.handle===0&&!found.catalog.loader.sources.has(key)});
            const handle=palettes.load(id,a.title.backgroundPalette.banks);m.discard(handle);
            focused.push({name:'discard retains the source backlink for reload',passed:found.entry.handle===handle&&found.catalog.loader.sources.get(key)===handle&&m.handle(handle).segment===0});
            const reloaded=c.loadSource(found.catalog.handle,'SHPL',id);
            focused.push({name:'discarded palette reload uses its existing handle and original bytes',passed:reloaded===handle&&m.resourcePayloads.get(handle)[4]===found.entry.payload[4]});
            m.freeHandle(handle);const replacement=m.allocateHandle(8);
            focused.push({name:'reused handle cannot retain the freed source backlink',passed:replacement===handle&&found.entry.handle===0&&!found.catalog.loader.sources.has(key)&&!m.resourceOwners.has(handle)});
          }
          catch(e){error=String(e);}
          return {stages,focused,error,instructionObserverLoaded:typeof OriginalResourceWork!=='undefined'};
        }''',dict(inputs=inputs,title=title,entrance=entrance,entranceConfig=entrance_config,selection=selection,room=room,roomConfig=room_config,transfer=transfer,transferConfig=transfer_config,board=board,boardConfig=board_config,boardTables=tables if board else None));browser.close()
    checks=[]
    for stage,expected in fixtures.items():
        actual=result['stages'].get(stage,{})
        for field in ['arena','near','dos','files','catalogs']:
            equal=actual.get(field)==expected[field]
            check=dict(name=f'{stage} {field}',passed=equal)
            if equal:check['state_sha256']=hashlib.sha256(json.dumps(expected[field],sort_keys=True,separators=(',',':')).encode()).hexdigest()
            else:check.update(expected=expected[field],actual=actual.get(field))
            checks.append(check)
        payloads={i:hashlib.sha256(base64.b64decode(b,validate=True)).hexdigest() for i,b in actual.get('payloads',[])}
        checks.append(dict(name=f'{stage} modeled source/font/cursor/sound payloads',passed=bool(payloads) and all(expected['payloads'].get(i)==sha for i,sha in payloads.items()),
            compared=len(payloads),differences={i:dict(expected=expected['payloads'].get(i),actual=sha) for i,sha in payloads.items() if expected['payloads'].get(i)!=sha}))
    report=dict(passed=not result['error'] and not result['instructionObserverLoaded'] and all(c['passed'] for c in checks+result['focused']),checks=checks,focused=result['focused'],error=result['error'],
        stage_names=list(result['stages']),models={n:digest(ROOT/'treehouse-demo'/n) for n in modules},references=references,
        full_game_parity=False,playable_changed=False,
        scope='Continuous executable/platform/archive-generated resource memory through startup. Native boundaries compare complete allocator, DOS, archive directories and active modeled source/font/cursor/sound payloads. No captured initial heap, allocation requests or resource addresses drive this model. Supplied semantic gameplay inputs are listed separately below. This is resource ownership at semantic script/sound completion, not animation/pixel/audio timing parity. Converted shape/surface payloads, later activity lifetimes and playable integration remain separate.')
    report['entrance_preparation']=entrance
    report['selection']=selection
    report['room']=room
    report['transfer']=transfer
    report['board']=board
    if entrance:report['scope']+=' Also includes six interface palettes, child-selection backdrop and decorations, two child palettes, saved-rectangle lifetimes, all three first-display child previews, background music ownership and final ready state. Pixel/script/audio scheduling and actual input remain separate.'
    if selection:
        report['selection_semantic_inputs']=dict(cloud=5,credit_changes=2,source='New-game cloud default and the two visible credit changes in the ordinary-input capture. These drive semantic resource operations, not native allocation requests or addresses. Live timer integration is not verified.')
        report['scope']+=' Extends continuously through supplied semantic entrance-idle events, the selected child and other child animations, the selected child climbing, and release of both child palettes and all four saved character backgrounds. Script playback advances to semantic completion; native clock or live event scheduling is not generated by this check.'
    if room:
        report['room_semantic_inputs']=dict(cloud=5,hour=12,minute=0,objects=[o['type'] for o in room_config['objects']],source='Pinned new-game defaults and executable object tables. Time progression and live renderer integration remain separate.')
        report['scope']+=' Extends through child-archive opening and initial interior resource construction, comparing intermediate boundaries as well as final ownership. Money-game integration remains separate.'
    if transfer:report['scope']+=' Also covers the board-transition entry seam, opening-ring construction and semantic script playback, child-backing replacement, inlet opening, bubble construction/playback, sound replacement, transition cleanup and room teardown. Default central-room objects only. Live event integration remains unimplemented; clock advancement and semantic sound completion in this resource check are not timing-parity claims.'
    if board:
        report['board_semantic_input']=dict(entry_seed=board_config['entrySeed'],source='Single RNG seed at native board entry, supplied to the existing BoardGame algorithm. It generates the nodes, directions and board types; no captured allocation or shape-call sequence is supplied. Upstream RNG/clock integration remains unverified.')
        report['scope']+=' Extends board entry through its six palettes, complete initial board drawing and options screen resource construction/cleanup. One native entry RNG seed is a semantic input to the gameplay model. Later gameplay resource events and live integration are not yet covered; this does not prove converted pixels or timing.'
    report['elapsed_seconds']=time.perf_counter()-started
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),focused=report['focused'],error=report['error'],stages=report['stage_names'],failed=[c['name'] for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--entrance',action='store_true')
    p.add_argument('--selection',choices=['boy','girl'])
    p.add_argument('--room',action='store_true')
    p.add_argument('--transfer',action='store_true')
    p.add_argument('--board',action='store_true')
    a=p.parse_args();raise SystemExit(0 if verify(a.output,a.entrance,a.selection,a.room,a.transfer,a.board) else 1)
