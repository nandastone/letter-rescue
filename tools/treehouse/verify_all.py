"""Run reconstruction regressions against one immutable candidate build."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse,hashlib,json,subprocess,sys
SUITES=['demo','entrance','theater','theater_playback','nature','continuation','chalkboard','boardgame','music_followup','music_editor','music_maze','room','character','rewards','music_completion','nature_completion','objects','persistence','help','board_completion','maze_generation','reward_completion','board_sequence','global_controls','guidance','room_sequence','nature_guidance','audio_ownership','room_transitions','exterior','exterior_sequence','telescope_journey','journeys','shelf_sequence','nature_sequence','timing','animation_resources','input_lifecycle','winning_journeys']

SUITES += ['maze_journeys', 'board_journeys', 'session_journey', 'maze_native_journey', 'board_native_journey', 'board_native_completion', 'maze_exit', 'audio_output', 'board_money_loss', 'board_payment_rng']
SUITES += ['nature_prize']
SUITES += ['nature_native_journey']
SUITES += ['theater_wrap']
SUITES += ['theater_prop_save']
SUITES += ['nature_editing_native', 'nature_editing_save']
SUITES += ['nature_remove_sound']
SUITES += ['music_journey', 'music_native_journey']
SUITES += ['music_preferences', 'music_preferences_native']
SUITES += ['room_action_continuity', 'theater_native_journey']
SUITES += ['audio_sustain']
SUITES += ['theater_notebook']
SUITES += ['board_payment_large']
SUITES += ['yard_interactions']
SUITES += ['calendar_journey']
SUITES += ['room_navigation']
SUITES += ['room_clock', 'chalk_native_stroke']
SUITES += ['room_native_journey']
SUITES += ['room_care_journey']
SUITES += ['room_drag_journey']
SUITES += ['plane_native_journey', 'caterpillar_native_journey']
SUITES += ['object_press']
SUITES += ['board_loss_ending']
SUITES += ['audio_stop', 'audio_instruments']
SUITES += ['audio_mixer_lifecycle']
SUITES += ['theater_audio_events']
SUITES += ['nature_audio_events']
SUITES += ['board_audio_events']
SUITES += ['maze_audio_events']
SUITES += ['maze_transfer']
SUITES += ['piano_note']
SUITES += ['maze_difficulty']
SUITES += ['theater_shuffle']
SUITES += ['piano_held']
SUITES += ['telescope_centering']
SUITES += ['telescope_views']
SUITES += ['telescope_input']
SUITES += ['theater_room_input']
SUITES += ['maze_sound_loading']
SUITES += ['theater_presentation_controls']
SUITES += ['earned_prize']
SUITES += ['need_warnings']
SUITES += ['balloon_clearance']
SUITES += ['basket_handoff', 'stationary_drag']

def main(html,output):
    output.mkdir(parents=True,exist_ok=False);digest=hashlib.sha256(html.read_bytes()).hexdigest()
    def run(suite):
        result=subprocess.run([sys.executable,str(Path(__file__).with_name(f'verify_{suite}.py')),'--html',str(html),'--output',str(output/suite)],capture_output=True,text=True,encoding='utf-8',errors='replace')
        (output/f'{suite}.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        path=output/suite if (output/suite).is_file() else output/suite/'report.json';report=json.loads(path.read_text(encoding='utf-8'))if path.exists()else{}
        passed=result.returncode==0 and bool(report) and report.get('passed',report.get('behavior_passed',True)) and not report.get('errors')
        if 'total' in report:passed=passed and report.get('exact')==report['total']
        for item in report.get('pixels',report.get('pixel_comparisons',{})).values():passed=passed and item.get('exact',False)
        return suite,dict(passed=bool(passed),exit_code=result.returncode,report=str(path),result=report)
    reports={}
    with ThreadPoolExecutor(max_workers=3)as pool:
        for future in as_completed([pool.submit(run,s)for s in SUITES]):
            suite,result=future.result();reports[suite]=result;print(suite,'PASS'if result['passed']else'FAIL',flush=True)
    unchanged=hashlib.sha256(html.read_bytes()).hexdigest()==digest
    bundle=dict(demo_sha256=digest,build_unchanged=unchanged,passed=unchanged and all(r['passed']for r in reports.values()),suites=reports)
    (output/'report.json').write_text(json.dumps(bundle,indent=2),encoding='utf-8');print('ALL PASS'if bundle['passed']else'FAILURES',flush=True)
    return 0 if bundle['passed']else 1

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(main(a.html,a.output))
