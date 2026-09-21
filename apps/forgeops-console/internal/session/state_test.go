package session

import (
	"context"
	"testing"
	"time"
)

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

func TestScopeGenerationRequiresListedNamespaceAndCancelsOlderRequests(t *testing.T) {
	state, err := New([]string{"dev"})
	if err != nil {
		t.Fatal(err)
	}
	first, err := state.SelectContext("dev")
	if err != nil || first.Generation != 1 || first.Namespace != "" {
		t.Fatalf("unexpected context scope %#v %v", first, err)
	}
	requestContext, cancel, _, err := state.RequestContext(context.Background(), first.Generation)
	if err != nil {
		t.Fatal(err)
	}
	defer cancel()
	if _, err := state.SelectNamespace("default"); err != ErrUnknownNamespace {
		t.Fatalf("expected unlisted namespace rejection, got %v", err)
	}
	if err := state.AllowNamespaces(first.Generation, []string{"default"}); err != nil {
		t.Fatal(err)
	}
	second, err := state.SelectNamespace("default")
	if err != nil || second.Generation != 2 || second.Namespace != "default" {
		t.Fatalf("unexpected namespace scope %#v %v", second, err)
	}
	select {
	case <-requestContext.Done():
	case <-time.After(time.Second):
		t.Fatal("scope change did not cancel older request")
	}
	if _, _, _, err := state.RequestContext(context.Background(), first.Generation); err != ErrStaleScope {
		t.Fatalf("expected stale generation, got %v", err)
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

func TestNamespaceSelectionRejectsOldGenerationWithoutChangingScope(t *testing.T) {
	state, _ := New([]string{"dev"})
	first, _ := state.SelectContext("dev")
	_ = state.AllowNamespaces(first.Generation, []string{"team"})
	second, err := state.SelectNamespaceAt("team", first.Generation)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = state.SelectNamespaceAt("team", first.Generation); err != ErrStaleScope {
		t.Fatal("old namespace selection accepted")
	}
	if state.Current() != second {
		t.Fatal("rejection changed scope")
	}
}
