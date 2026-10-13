"""Extract resource-ownership inputs from the pinned executable and archives.

These are source resources and launch-platform parameters. Native RAM snapshots,
allocation observations, clocks and captured resource addresses are not inputs.
"""
import base64
import hashlib
import struct
import zipfile

from build_demo import SOURCE_SHA
from executable import unpack, disassemble_script
from resources import parse_archive


def scene_inputs(archive, exe, image, metadata):
    overlay = next(o for o in metadata['overlays'] if o['id'] == 5)
    code = exe[overlay['file_offset'] + overlay['header_bytes']:overlay['file_offset'] + overlay['size']]
    word = lambda offset: struct.unpack_from('<H', code, offset)[0]
    assert all(code[at] == 0xb8 for at in [0x20f, 0x213, 0x287, 0x28b, 0x297])
    background = dict(id=word(0x210), banks=word(0x214))
    animation = dict(id=word(0x288), banks=word(0x28c))
    data = archive.read('TheTreeh/th.dat')
    entries = parse_archive(data)

    def script(identifier, source=data):
        entry = next(r for r in parse_archive(source) if r['tag'] == 'SCR' and r['id'] == identifier)
        decoded = disassemble_script(source[entry['payload_offset']:entry['payload_offset'] + entry['size']], image)
        return dict(bounds=decoded['bounds_words'], code=[[op['opcode'], list(bytes.fromhex(op['operand_hex']))]
                                                        for op in decoded['instructions']])

    assert code[0x2b2:0x2b5] == bytes.fromhex('837ec6') and image[0x4a56] == 0xb8
    origins = [list(reversed(struct.unpack_from('<2h', image, 0x321d0 + 0x14c0 + 4*i))) for i in range(code[0x2b5])]
    title = dict(backgroundPalette=background, animationPalette=animation, sound=word(0x298),
                 backgroundBounds=list(struct.unpack_from('<4h', image, 0x321d0 + 0x14b8)),
                 animationOrigin=origins[0], animationOrigins=origins,
                 querySound=struct.unpack_from('<H', image, 0x4a57)[0], script=script(animation['id']))
    palette = lambda offset: dict(id=struct.unpack_from('<H', image, offset+1)[0],
                                  banks=struct.unpack_from('<H', image, offset+5)[0])
    ui = [palette(0x547 + 16*i) for i in range(6)]
    children = [palette(at) for at in [0xb9b, 0xbab]]
    scripts = [script(c['id']) for c in children + [dict(id=children[0]['id']+i) for i in [2, 3]]]
    saved_offsets = [struct.unpack_from('<H', image, at)[0] for at in [0xbc9, 0xbd6, 0xbe3]]
    entrance = dict(palettes=ui, childPalettes=children,
                    screenBounds=list(struct.unpack_from('<4h', image, 0x321d0 + 0x15f8)),
                    savedBounds=[list(struct.unpack_from('<4h', image, 0x321d0 + at)) for at in saved_offsets],
                    postPreviewBounds=[list(struct.unpack_from('<4h', image, 0x321d0 + struct.unpack_from('<H', image, at)[0]))
                                       for at in [0xc0f, 0xc43]],
                    music=struct.unpack_from('<H', image, 0xcfd)[0], querySound=title['querySound'],
                    script=scripts[0], scripts=scripts,
                    creditBounds=list(struct.unpack_from('<4h', image, 0x321d0 + 0x142c)))
    rooms = {}
    ds = 0x321d0
    for sex, child in enumerate(['boy', 'girl']):
        name_offset = struct.unpack_from('<H', image, ds+0x248+2*sex)[0]
        filename = image[ds+name_offset:].split(b'\0', 1)[0].decode('ascii')
        member = next(n for n in archive.namelist() if n.lower() == 'thetreeh/'+filename.lower())
        character_bounds = list(struct.unpack_from('<4h', image, ds+0x1c4))
        if not sex:
            character_bounds[0] += 4
        rooms[child] = dict(palettes=[palette(at) for at in [0x1ff1, 0x2001, 0x2011, 0x2021, 0x2031]],
                           screenBounds=entrance['screenBounds'],
                           theaterBounds=list(struct.unpack_from('<4h', image, 0x2e8f0+0x48+0x68)),
                           characterBounds=character_bounds,
                           # Callers select live objects/time/cloud; these are source tables only.
                           objectDefinitions=[dict(type=i, palette=[870, 900, 930][struct.unpack_from('<H', image, ds+0x5f6+2*i)[0]],
                                                   relative=struct.unpack_from('<H', image, ds+0x936+10*i+2)[0],
                                                   bounds=list(struct.unpack_from('<4h', image, ds+0x7be+8*i))) for i in [9, 20, 8, 10, 6]],
                           archive=dict(archive=base64.b64encode(archive.read(member)).decode('ascii'), filename='C:\\THETREEH\\'+filename))
    transfer_palette = palette(0x5217)
    transfer = dict(palette=transfer_palette, sound=struct.unpack_from('<H', image, 0x5234)[0],
                    script=script(transfer_palette['id']),
                    bubble=dict(id=1103, querySound=title['querySound'],
                                inletBounds=list(struct.unpack_from('<4h', image, ds+0x3d6)), script=script(1103)))
    overlay3 = next(o for o in metadata['overlays'] if o['id'] == 3)
    board_code = exe[overlay3['file_offset']+overlay3['header_bytes']:overlay3['file_offset']+overlay3['size']]
    board_palettes = []
    for at in range(0x20, 0x80, 0x10):
        assert board_code[at] == board_code[at+4] == 0xb8
        board_palettes.append(dict(id=struct.unpack_from('<H', board_code, at+1)[0], banks=struct.unpack_from('<H', board_code, at+5)[0]))
    assert board_code[0x693] == 0x05 and board_code[0x6a5] == 0xb8
    board = dict(palettes=board_palettes, screenBounds=entrance['screenBounds'],
                 backgroundPalette=dict(id=10*struct.unpack_from('<H', board_code, 0x694)[0], banks=struct.unpack_from('<H', board_code, 0x6a6)[0]),
                 optionsPalette=dict(id=struct.unpack_from('<H', board_code, 0xb1f)[0], banks=struct.unpack_from('<H', board_code, 0xb23)[0]))
    board['clickSound'] = struct.unpack_from('<H', image, 0x5ba5)[0]
    board['querySound'] = title['querySound']
    board['dashboards'] = []
    source = archive.read('TheTreeh/modules.dat')
    for role in range(3):
        identifier = (struct.unpack_from('<H', board_code, 0x39f1)[0]+role)*struct.unpack_from('<H', board_code, 0x39f4)[0]
        board['dashboards'].append(dict(id=identifier, banks=struct.unpack_from('<H', board_code, 0x39e8)[0], script=script(identifier,source)))
    return dict(title=title, entrance=entrance, rooms=rooms, transfer=transfer, board=board)


def extract(source):
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('Resource startup requires the pinned DOS 1.1 archive')
    with zipfile.ZipFile(source) as archive:
        exe = archive.read('TheTreeh/treehse.exe')
        image, metadata = unpack(exe)
        mz = struct.unpack_from('<14H', exe)
        packed = struct.unpack_from('<9H', exe, 16 * (mz[4] + mz[11]))
        assert mz[6] == 65535 and image[0xd593] == 0xbf and image[0xd5a8:0xd5aa] == b'\x81\xc4'
        config_name = image[0x321d0 + 0x89:].split(b'\0', 1)[0].decode('ascii').lower()
        startup = dict(dataSegmentRelative=struct.unpack_from('<H', image, 0xd594)[0],
                       stackPointer=packed[4], stackBias=struct.unpack_from('<H', image, 0xd5aa)[0],
                       configurationBytes=len(archive.read('TheTreeh/' + config_name)),
                       screenHeight=struct.unpack_from('<H', image, 0xd510 + 0x9ce4 + 8)[0],
                       environment=['PATH=Z:\\', 'COMSPEC=Z:\\COMMAND.COM', 'BLASTER=A220 I7 D1 H5 T6'])
        builtins = {}
        for index, tag in enumerate(['FONT', 'CURS']):
            entry = image[0x31660 + 10 + 15 * index:0x31660 + 25 + 15 * index]
            assert entry[:4] == tag.encode()[::-1] and entry[4:6] == b'\0\0'
            offset, segment, length = struct.unpack_from('<HHH', entry, 6)
            payload = image[16 * segment + offset:16 * segment + offset + length]
            assert len(payload) == length
            builtins[tag] = dict(payload=base64.b64encode(payload).decode('ascii'), flags=entry[12])
        names = ['th.dat', 'ibm_snd.dat']
        names.extend(image[0x321d0 + offset:].split(b'\0', 1)[0].decode('ascii')
                     for offset in [0x155, 0x161, 0x16c, 0x184, 0x18d])
        archives = [dict(archive=base64.b64encode(archive.read('TheTreeh/' + name)).decode('ascii'),
                         filename='C:\\THETREEH\\' + name) for name in names]
        scenes = scene_inputs(archive, exe, image, metadata)
    descriptor = struct.unpack_from('<H', image, 0x321d0 + 0x20b4 + 2 * 5)[0]
    pixels_per_byte = image[0xd510 + descriptor + 6]
    assert pixels_per_byte == 1 and image[0x21c10] == 0xb9 and image[0x21c13] == 0xba
    rates = dict(minimumRate=struct.unpack_from('<H', image, 0x21c11)[0],
                 maximumRate=struct.unpack_from('<H', image, 0x21c14)[0])
    return dict(startup=startup, builtins=builtins, pixelsPerByte=pixels_per_byte,
                soundRateLimits=rates, archives=archives, volume='REFERENCE-S',
                savedRectangle=list(struct.unpack_from('<4h', image, 0x2e8f0 + 0x140)), scenes=scenes)
