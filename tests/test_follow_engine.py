from easyabc2.engines.follow_engine import FollowScoreEngine, TimedSvgNote

calls = []

def mock_js(code):
    calls.append(code)
    
def test_follow_incomplete_abc():
    fe = FollowScoreEngine(score_js=mock_js, preferences=None)

    cases = [
        "X:1\n",
        "X:1\nT:Test\n",
        "X:1\nT:Test\nM:4/4\n",
        "X:1\nT:Test\nM:4/4\nK:C\n",
        "X:1\nT:Test\nM:4/4\nK:C\nC\n",
        "X:1\nT:Test\nM:4/4\nK:C\nC D E F\n",
    ]

    i=0
    for abc in cases:
        i+=1
        fe.build2(abc, [])
        print(f"timed notes case {i}: {fe.timed_notes}")

def test_follow_OK():
    fe = FollowScoreEngine(score_js=mock_js, preferences=None)

    abc="""X:1
T:Test
M:4/4
K:C
C D E F
"""
    
    midi_events = [
        {'row': 5, 'col': 1, 'start_tick': 0, 'stop_tick': 240},
        {'row': 5, 'col': 3, 'start_tick': 240, 'stop_tick': 480},
        {'row': 5, 'col': 5, 'start_tick': 480, 'stop_tick': 720},
        {'row': 5, 'col': 7, 'start_tick': 720, 'stop_tick': 960},
    ]
    
    fe.build2(abc, midi_events)
    print(f"timed notes case OK: {fe.timed_notes}")

def test_build_events_OK():
    fe = FollowScoreEngine(score_js=mock_js, preferences=None)
    fe.timed_notes = [
        TimedSvgNote(start_id=10, rect_index=0, line=4, col=0, tick_intervals=[(0, 240)])
    ]
    fe._build_events()

    assert fe.events == [
        (0, "on", fe.timed_notes[0]),
        (240, "off", fe.timed_notes[0])
    ]

def test_on_tick_OK():
    fe = FollowScoreEngine(score_js=mock_js, preferences=None)
    note = TimedSvgNote(start_id=10, rect_index=0, line=4, col=0, tick_intervals=[(0, 240)])
    fe.events = [
        (0, "on", note),
        (240, "off", note)
    ]

    fe.on_tick(0, is_visual=False)
    assert fe.active_notes == {note.start_id}

    fe.on_tick(240, is_visual=False)
    assert fe.active_notes == set()


if __name__ == "__main__":
    test_follow_incomplete_abc()
    test_follow_OK()
    test_build_events_OK()
    test_on_tick_OK()
    print(f"no expected calls: {calls}")