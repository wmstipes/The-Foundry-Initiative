package plugins

import (
	"errors"
	"fmt"
	"regexp"
)

const (
	SDKVersion             = "0.1.0"
	SupportedSDKConstraint = ">=0.1.0 <0.2.0"
	DashboardCard          = "dashboardCard"
)

var (
	idPattern      = regexp.MustCompile(`^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$`)
	versionPattern = regexp.MustCompile(`^[0-9]+\.[0-9]+\.[0-9]+$`)
)

type Contribution struct {
	ID         string `json:"id"`
	Type       string `json:"type"`
	Title      string `json:"title"`
	Capability string `json:"capability"`
}

type Manifest struct {
	ID               string         `json:"id"`
	DisplayName      string         `json:"displayName"`
	Version          string         `json:"version"`
	SDKCompatibility string         `json:"sdkCompatibility"`
	Capabilities     []string       `json:"capabilities"`
	Contributions    []Contribution `json:"contributions"`
}

func (m Manifest) Validate() error {
	if !idPattern.MatchString(m.ID) {
		return errors.New("plugin ID is invalid")
	}
	if m.DisplayName == "" {
		return errors.New("plugin display name is required")
	}
	if !versionPattern.MatchString(m.Version) {
		return errors.New("plugin version must be a three-part semantic version")
	}
	if m.SDKCompatibility != SupportedSDKConstraint {
		return fmt.Errorf("unsupported SDK compatibility %q", m.SDKCompatibility)
	}

	capabilities := make(map[string]struct{}, len(m.Capabilities))
	for _, capability := range m.Capabilities {
		if !idPattern.MatchString(capability) {
			return errors.New("capability ID is invalid")
		}
		if _, exists := capabilities[capability]; exists {
			return errors.New("capability IDs must be unique")
		}
		capabilities[capability] = struct{}{}
	}

	contributions := make(map[string]struct{}, len(m.Contributions))
	for _, contribution := range m.Contributions {
		if !idPattern.MatchString(contribution.ID) {
			return errors.New("contribution ID is invalid")
		}
		if _, exists := contributions[contribution.ID]; exists {
			return errors.New("contribution IDs must be unique")
		}
		contributions[contribution.ID] = struct{}{}
		if contribution.Type != DashboardCard {
			return fmt.Errorf("unsupported contribution type %q", contribution.Type)
		}
		if contribution.Title == "" {
			return errors.New("contribution title is required")
		}
		if _, declared := capabilities[contribution.Capability]; !declared {
			return fmt.Errorf("contribution references undeclared capability %q", contribution.Capability)
		}
	}
	return nil
}

func (m Manifest) Declares(capability string) bool {
	for _, declared := range m.Capabilities {
		if declared == capability {
			return true
		}
	}
	return false
}
