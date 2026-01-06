#!/usr/bin/env python3
"""
BamBam Adaptive Learning Profiles

Tracks child engagement and preferences to optimize the learning experience.
Stores profile data in ~/.config/bambam/profiles/
"""

import json
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


_YAML_AVAILABLE = False
try:
    import yaml  # noqa: F401
    _YAML_AVAILABLE = True
except ImportError:
    pass


class ChildProfile:
    """Represents a child's learning profile with engagement tracking."""

    def __init__(self, name: str, config_dir: Optional[Path] = None):
        self.name = name
        self.config_dir = config_dir or Path.home() / '.config' / 'bambam' / 'profiles'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profile_file = self.config_dir / f"{name.lower().replace(' ', '_')}.json"

        # Profile data
        self.data = {
            'name': name,
            'created': datetime.now().isoformat(),
            'age_months': None,
            'total_sessions': 0,
            'total_playtime_seconds': 0,
            'key_counts': defaultdict(int),
            'sound_engagement': defaultdict(float),
            'image_engagement': defaultdict(float),
            'extension_engagement': defaultdict(float),
            'theme_engagement': defaultdict(float),
            'favorite_letters': [],
            'session_history': [],
            'last_session': None,
        }

        # Current session tracking
        self._session_start = None
        self._session_events = []
        self._current_extension = None
        self._current_theme = None

        self._load()

    def _load(self):
        """Load profile from disk."""
        if self.profile_file.exists():
            try:
                with open(self.profile_file) as f:
                    saved_data = json.load(f)
                    # Merge with defaults for new fields
                    for key, value in saved_data.items():
                        if key in self.data:
                            if isinstance(self.data[key], defaultdict):
                                self.data[key] = defaultdict(
                                    type(list(self.data[key].values())[0]) if self.data[key] else float,
                                    value
                                )
                            else:
                                self.data[key] = value
            except (json.JSONDecodeError, IOError):
                pass  # Use defaults

    def save(self):
        """Save profile to disk."""
        # Convert defaultdicts to regular dicts for JSON
        save_data = {}
        for key, value in self.data.items():
            if isinstance(value, defaultdict):
                save_data[key] = dict(value)
            else:
                save_data[key] = value

        with open(self.profile_file, 'w') as f:
            json.dump(save_data, f, indent=2, default=str)

    def start_session(self, extension: Optional[str] = None, theme: Optional[str] = None):
        """Start a new play session."""
        self._session_start = time.time()
        self._session_events = []
        self._current_extension = extension
        self._current_theme = theme

    def end_session(self):
        """End the current session and save stats."""
        if self._session_start is None:
            return

        duration = time.time() - self._session_start
        self.data['total_sessions'] += 1
        self.data['total_playtime_seconds'] += duration
        self.data['last_session'] = datetime.now().isoformat()

        # Calculate session summary
        session_summary = {
            'date': datetime.now().isoformat(),
            'duration_seconds': int(duration),
            'event_count': len(self._session_events),
            'extension': self._current_extension,
            'theme': self._current_theme,
        }

        # Keep last 100 sessions
        self.data['session_history'].append(session_summary)
        self.data['session_history'] = self.data['session_history'][-100:]

        # Update favorite letters
        self._update_favorites()

        self.save()
        self._session_start = None

    def record_keypress(self, key: str, sound_played: Optional[str] = None,
                        image_shown: Optional[str] = None):
        """Record a keypress event."""
        self.data['key_counts'][key] = self.data['key_counts'].get(key, 0) + 1

        event = {
            'time': time.time() - (self._session_start or time.time()),
            'key': key,
            'sound': sound_played,
            'image': image_shown,
        }
        self._session_events.append(event)

        # Update engagement scores based on response time patterns
        # (rapid repeated presses indicate engagement)
        if len(self._session_events) >= 2:
            time_diff = self._session_events[-1]['time'] - self._session_events[-2]['time']
            if time_diff < 2.0:  # Quick succession = engagement
                engagement_boost = max(0.1, 1.0 - time_diff)
                if sound_played:
                    self.data['sound_engagement'][sound_played] = (
                        self.data['sound_engagement'].get(sound_played, 0.5) * 0.9 +
                        engagement_boost * 0.1
                    )
                if image_shown:
                    self.data['image_engagement'][image_shown] = (
                        self.data['image_engagement'].get(image_shown, 0.5) * 0.9 +
                        engagement_boost * 0.1
                    )

    def record_extension_engagement(self, extension: str, engagement_score: float):
        """Record engagement with a specific extension."""
        current = self.data['extension_engagement'].get(extension, 0.5)
        # Exponential moving average
        self.data['extension_engagement'][extension] = current * 0.8 + engagement_score * 0.2

    def record_theme_engagement(self, theme: str, engagement_score: float):
        """Record engagement with a specific theme."""
        current = self.data['theme_engagement'].get(theme, 0.5)
        self.data['theme_engagement'][theme] = current * 0.8 + engagement_score * 0.2

    def _update_favorites(self):
        """Update favorite letters based on key counts."""
        if not self.data['key_counts']:
            return

        # Get top 5 most pressed letter keys
        letter_counts = {
            k: v for k, v in self.data['key_counts'].items()
            if len(k) == 1 and k.isalpha()
        }
        sorted_letters = sorted(letter_counts.items(), key=lambda x: x[1], reverse=True)
        self.data['favorite_letters'] = [k for k, v in sorted_letters[:5]]

    def get_suggested_extension(self, available_extensions: list) -> Optional[str]:
        """Get the suggested extension based on engagement history."""
        if not available_extensions:
            return None

        if not self.data['extension_engagement']:
            return available_extensions[0]

        # Sort by engagement, prefer extensions with higher scores
        scored = [
            (ext, self.data['extension_engagement'].get(ext, 0.5))
            for ext in available_extensions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]

    def get_suggested_theme(self, available_themes: list) -> Optional[str]:
        """Get the suggested theme based on engagement history."""
        if not available_themes:
            return None

        if not self.data['theme_engagement']:
            return available_themes[0]

        scored = [
            (theme, self.data['theme_engagement'].get(theme, 0.5))
            for theme in available_themes
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]

    def get_stats_summary(self) -> dict:
        """Get a summary of profile statistics."""
        total_time = timedelta(seconds=int(self.data['total_playtime_seconds']))
        return {
            'name': self.data['name'],
            'total_sessions': self.data['total_sessions'],
            'total_playtime': str(total_time),
            'favorite_letters': self.data['favorite_letters'],
            'last_session': self.data['last_session'],
            'top_extensions': sorted(
                self.data['extension_engagement'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3],
            'top_themes': sorted(
                self.data['theme_engagement'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3],
        }


class ProfileManager:
    """Manages multiple child profiles."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / '.config' / 'bambam' / 'profiles'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._profiles: dict[str, ChildProfile] = {}
        self._active_profile: Optional[ChildProfile] = None

    def list_profiles(self) -> list[str]:
        """List all available profile names."""
        profiles = []
        for f in self.config_dir.glob('*.json'):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    profiles.append(data.get('name', f.stem))
            except (json.JSONDecodeError, IOError):
                profiles.append(f.stem)
        return profiles

    def get_profile(self, name: str) -> ChildProfile:
        """Get or create a profile by name."""
        if name not in self._profiles:
            self._profiles[name] = ChildProfile(name, self.config_dir)
        return self._profiles[name]

    def set_active_profile(self, name: str) -> ChildProfile:
        """Set the active profile."""
        self._active_profile = self.get_profile(name)
        return self._active_profile

    def get_active_profile(self) -> Optional[ChildProfile]:
        """Get the currently active profile."""
        return self._active_profile

    def delete_profile(self, name: str) -> bool:
        """Delete a profile."""
        profile = self._profiles.get(name)
        if profile and profile.profile_file.exists():
            profile.profile_file.unlink()
            del self._profiles[name]
            if self._active_profile and self._active_profile.name == name:
                self._active_profile = None
            return True
        return False


# Convenience function for integration
def create_default_profile() -> ChildProfile:
    """Create a default profile for single-child use."""
    return ChildProfile("default")


if __name__ == '__main__':
    # Demo/test
    profile = ChildProfile("Test Child")
    profile.start_session(extension="alphanumeric-en_US", theme="default")

    # Simulate some keypresses
    for key in ['a', 'b', 'a', 'c', 'a', 'd', 'a']:
        profile.record_keypress(key, sound_played=f"{key}.ogg")
        time.sleep(0.1)

    profile.end_session()
    print("Profile stats:", profile.get_stats_summary())
