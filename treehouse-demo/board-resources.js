"use strict";
// Resource ownership for overlay 3. OriginalStartupResources supplies the
// shared catalog/sound/shape operations; the caller owns gameplay and pixels.
class OriginalBoardResources {
  static prepare(state,{palettes},observe=()=>{}){
    if(state.entrancePhase!=='room-released')throw new Error("Board entry requires room release");
    OriginalStartupResources.selectCursor(state,1);
    state.boardPalettes=new Map();
    const loader=new OriginalPaletteLoading(state.catalogs);
    observe('board-before',state);
    for(const palette of palettes){
      state.boardPalettes.set(palette.id,loader.load(palette.id,palette.banks));
      observe(`board-palette-${palette.id}`,state);
    }
    state.entrancePhase='board-prepared';
  }
  static beginDrawing(state,{screenBounds,backgroundPalette},observe=()=>{}){
    if(state.entrancePhase!=='board-prepared')throw new Error("Board palettes are not prepared");
    const m=state.memory,[top,left,bottom,right]=screenBounds;
    // Overlay 3:625 draws the board on a temporary full-screen surface.
    state.boardSurface={rows:m.near.allocate(2*(bottom-top)),pixels:m.allocateRaw((bottom-top)*(right-left))};
    m.freeHandle(OriginalStartupResources.loadShape(state,state.boardPalettes.get(4000),1));
    observe('board-background-before',state);
    state.boardBackgroundPalette=new OriginalPaletteLoading(state.catalogs).load(backgroundPalette.id,backgroundPalette.banks);
    state.entrancePhase='board-background-prepared';observe('board-background-after',state);
  }
  static prepareOptions(state,{screenBounds,gameRects,optionsPalette},game,observe=()=>{}){
    if(state.entrancePhase!=='board-background-prepared')throw new Error("Board background is not prepared");
    if(game.mode!==0||game.opponent!==2||game.player!==0)throw new Error("Board resource drawing currently covers the initial money/robot game");
    const m=state.memory,c=state.catalogs;
    const temporary=bounds=>{const [t,l,b,r]=bounds;return {rows:m.near.allocate(2*(b-t)),pixels:m.allocateRaw((b-t)*(r-l))};};
    const release=s=>{m.freeRaw(s.pixels);m.near.free(s.rows);};
    const draw=(palette,relative)=>m.freeHandle(OriginalStartupResources.loadShape(state,palette,relative));
    const drawBoard=(id,relative)=>draw(state.boardPalettes.get(id),relative);
    draw(state.boardBackgroundPalette,1);m.discardable(state.boardBackgroundPalette);state.boardBackgroundPalette=0;
    drawBoard(4000,3);drawBoard(4000,5);
    const strings=c.resolve('STRL',4000),text=c.loadSource(strings.catalog.handle,'STRL',4000);
    m.address(text);m.discardable(text);
    // Overlay 3:19EB/1A91 renders each place value on the union of the
    // coin-stack and number-label rectangles, then releases that surface.
    const balance=game.balances[0],digits=[Math.floor(balance/100),Math.floor(balance/10)%10,balance%10];
    for(let i=0;i<3;i++){
      const a=gameRects[7+i],b=gameRects[11+i];
      const surface=temporary([Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[2],b[2]),Math.max(a[3],b[3])]);
      for(let j=0;j<digits[i];j++)drawBoard(4400,5+i);
      release(surface);
    }
    draw(state.interfacePalettes.get(6),2);drawBoard(4400,1);
    for(const type of game.types)drawBoard(4400,type);
    drawBoard(4000,6);
    const hint=temporary(gameRects[2]);drawBoard(4400,25);release(hint);
    release(state.boardSurface);state.boardSurface=null;
    OriginalStartupResources.selectCursor(state,0);
    // Overlay 3:AC5 copies the board into its temporary options surface.
    state.boardOptionsSurface=temporary(screenBounds);
    observe('board-options-before',state);
    state.boardOptionsPalette=new OriginalPaletteLoading(c).load(optionsPalette.id,optionsPalette.banks);
    state.entrancePhase='board-options-prepared';observe('board-options-after',state);
  }
  static finishOptions(state,{optionsRects},game,observe=()=>{}){
    if(state.entrancePhase!=='board-options-prepared')throw new Error("Board options are not prepared");
    if(game.mode!==0||game.opponent!==2)throw new Error("Options resources currently cover money/robot settings");
    const m=state.memory,c=state.catalogs;
    const draw=(palette,relative)=>m.freeHandle(OriginalStartupResources.loadShape(state,palette,relative));
    const centered=(palette,relative,bounds)=>{
      const [t,l,b,r]=bounds,rows=m.near.allocate(2*(b-t)),pixels=m.allocateRaw((b-t)*(r-l));
      draw(palette,relative);m.freeRaw(pixels);m.near.free(rows);
    };
    const ui=state.interfacePalettes.get(6),board=state.boardPalettes.get(4400);
    draw(state.boardOptionsPalette,1);draw(state.boardPalettes.get(20200),1);
    // EAE, F64, 107D and 13FB, in the original options-paint order.
    draw(ui,3);centered(board,16,optionsRects[18]);
    draw(ui,3);centered(state.boardPalettes.get(24200),2,optionsRects[24]);
    draw(ui,3);centered(board,[31,30,28][game.levels[0]],optionsRects[19]);
    const strings=c.resolve('STRL',4000);
    for(let i=0;i<3;i++){
      // Resident 3CED paints filled labels through a temporary surface,
      // unlike the transparent 3CB0 text used on the game board itself.
      const [t,l,b,r]=optionsRects[11+i],rows=m.near.allocate(2*(b-t)),pixels=m.allocateRaw((b-t)*(r-l));
      const text=c.loadSource(strings.catalog.handle,'STRL',4000);m.address(text);m.discardable(text);
      m.freeRaw(pixels);m.near.free(rows);
    }
    observe('board-options-painted',state);
    m.freeRaw(state.boardOptionsSurface.pixels);m.near.free(state.boardOptionsSurface.rows);state.boardOptionsSurface=null;
    state.entrancePhase='board-options-ready';
  }
}
