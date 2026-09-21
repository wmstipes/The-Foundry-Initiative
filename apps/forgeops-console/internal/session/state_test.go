package session

import "testing"

func TestStateStartsUnselectedAndRejectsUnknownContext(t *testing.T) {
	state, err := New([]string{"zeta", "alpha"})
	if err != nil {
		t.Fatal(err)
	}
	if state.Selected() != "" {
		t.Fatalf("unexpected ambient selection %q", state.Selected())
	}
	if err := state.Select("missing"); err != ErrUnknownContext {
		t.Fatalf("expected unknown-context error, got %v", err)
	}
	if state.Selected() != "" {
		t.Fatal("failed selection changed state")
	}
	if err := state.Select("alpha"); err != nil {
		t.Fatal(err)
	}
	if state.Selected() != "alpha" {
		t.Fatalf("selection not retained in memory: %q", state.Selected())
	}
	names := state.ContextNames()
	if len(names) != 2 || names[0] != "alpha" || names[1] != "zeta" {
		t.Fatalf("unexpected names: %#v", names)
	}
}

func TestNonceIsRandomAndURLSafe(t *testing.T) {
	first, err := NewNonce()
	if err != nil {
		t.Fatal(err)
	}
	second, err := NewNonce()
	if err != nil {
		t.Fatal(err)
	}
	if first == second || len(first) < 40 || len(second) < 40 {
		t.Fatalf("nonces are not suitably distinct: %q %q", first, second)
	}
}
