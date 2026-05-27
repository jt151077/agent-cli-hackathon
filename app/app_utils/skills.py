# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from google.adk.skills import list_skills_in_dir
from google.adk.tools.skill_toolset import SkillToolset as BaseSkillToolset

class SkillManager:
    """Manages loading and indexing of agent skills from a directory."""
    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir
        # Ensure path is absolute to avoid issues with different working directories
        abs_skills_dir = os.path.abspath(skills_dir)
        self.skills = list_skills_in_dir(abs_skills_dir)

class SkillToolset(BaseSkillToolset):
    """Dynamic toolset that provides access to managed skills."""
    def __init__(self, skill_manager: SkillManager):
        super().__init__(skills=skill_manager.skills)

def get_ai_skills():
    """Helper to get a shared SkillToolset instance."""
    # We use a hardcoded relative path from the project root
    skill_manager = SkillManager(skills_dir="./skills")
    return SkillToolset(skill_manager)
