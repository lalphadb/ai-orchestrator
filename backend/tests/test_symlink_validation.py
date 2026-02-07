"""
Tests pour CRQ-P0-8: Validation Symlinks (Path Traversal Prevention)
"""

import os
import tempfile
from pathlib import Path

import pytest
from app.core.config import settings
from app.services.react_engine.tools import (is_path_in_workspace,
                                             validate_and_resolve_path)


class TestSymlinkValidation:
    """Tests pour la validation de symlinks et prévention path traversal"""

    def setup_method(self):
        """Créer un workspace temporaire pour les tests"""
        self.temp_workspace = tempfile.mkdtemp(prefix="test_workspace_")
        self.original_workspace = settings.WORKSPACE_DIR
        settings.WORKSPACE_DIR = self.temp_workspace

    def teardown_method(self):
        """Nettoyer le workspace temporaire"""
        settings.WORKSPACE_DIR = self.original_workspace
        # Nettoyer les fichiers/symlinks créés
        import shutil

        if os.path.exists(self.temp_workspace):
            shutil.rmtree(self.temp_workspace)

    def test_legitimate_file_in_workspace(self):
        """Fichier légitime dans workspace doit être accepté"""
        # Créer un fichier légitime
        legitimate_file = os.path.join(self.temp_workspace, "legitimate.txt")
        Path(legitimate_file).touch()

        # Validation via validate_and_resolve_path
        is_valid, result = validate_and_resolve_path("legitimate.txt", self.temp_workspace)
        assert is_valid, f"Fichier légitime refusé: {result}"

        # Validation via is_path_in_workspace
        is_valid, msg = is_path_in_workspace(legitimate_file)
        assert is_valid, f"Fichier légitime refusé par is_path_in_workspace: {msg}"

    def test_symlink_pointing_outside_workspace_blocked(self):
        """Symlink pointant hors workspace doit être bloqué (CRQ-P0-8)"""
        # Créer un symlink pointant vers /etc/passwd
        symlink_path = os.path.join(self.temp_workspace, "evil_link")
        try:
            os.symlink("/etc/passwd", symlink_path)
        except OSError:
            pytest.skip("Cannot create symlinks (permission denied)")

        # validate_and_resolve_path doit bloquer
        is_valid, result = validate_and_resolve_path("evil_link", self.temp_workspace)
        assert not is_valid, "Symlink malveillant non bloqué par validate_and_resolve_path"
        assert "outside workspace" in result.lower()

        # is_path_in_workspace doit bloquer
        is_valid, msg = is_path_in_workspace(symlink_path)
        assert not is_valid, "Symlink malveillant non bloqué par is_path_in_workspace"

    def test_symlink_pointing_inside_workspace_allowed(self):
        """Symlink pointant dans workspace doit être accepté"""
        # Créer un fichier cible dans workspace
        target_file = os.path.join(self.temp_workspace, "target.txt")
        Path(target_file).write_text("safe content")

        # Créer un symlink vers ce fichier
        symlink_path = os.path.join(self.temp_workspace, "safe_link")
        try:
            os.symlink(target_file, symlink_path)
        except OSError:
            pytest.skip("Cannot create symlinks (permission denied)")

        # validate_and_resolve_path doit accepter
        is_valid, result = validate_and_resolve_path("safe_link", self.temp_workspace)
        assert is_valid, f"Symlink sûr refusé: {result}"

        # is_path_in_workspace doit accepter
        is_valid, msg = is_path_in_workspace(symlink_path)
        assert is_valid, f"Symlink sûr refusé par is_path_in_workspace: {msg}"

    def test_path_traversal_with_dotdot_blocked(self):
        """Path traversal avec .. doit être bloqué"""
        # Tentative d'accès à /etc/passwd via ../../../etc/passwd
        traversal_path = "../../etc/passwd"

        is_valid, result = validate_and_resolve_path(traversal_path, self.temp_workspace)
        assert not is_valid, "Path traversal avec .. non bloqué"
        assert "traversal detected" in result.lower()

    def test_absolute_path_outside_workspace_blocked(self):
        """Chemin absolu hors workspace doit être bloqué"""
        absolute_outside = "/etc/passwd"

        is_valid, result = validate_and_resolve_path(absolute_outside, self.temp_workspace)
        assert not is_valid, "Chemin absolu hors workspace non bloqué"

    def test_symlink_chain_outside_workspace_blocked(self):
        """Chaîne de symlinks menant hors workspace doit être bloquée"""
        # Créer link1 -> link2 -> /etc/passwd
        link1 = os.path.join(self.temp_workspace, "link1")
        link2 = os.path.join(self.temp_workspace, "link2")

        try:
            os.symlink("/etc/passwd", link2)
            os.symlink(link2, link1)
        except OSError:
            pytest.skip("Cannot create symlinks (permission denied)")

        # La chaîne doit être bloquée
        is_valid, result = validate_and_resolve_path("link1", self.temp_workspace)
        assert not is_valid, "Chaîne de symlinks malveillante non bloquée"

        is_valid, msg = is_path_in_workspace(link1)
        assert not is_valid, "Chaîne de symlinks malveillante non bloquée par is_path_in_workspace"

    def test_relative_to_more_robust_than_startswith(self):
        """relative_to() est plus robuste que startswith() (CRQ-P0-8)"""
        # Cas edge: workspace = /home/user, path = /home/user_evil/file
        # startswith() pourrait accepter à tort si mal implémenté

        # Créer un répertoire similaire mais différent
        evil_workspace = self.temp_workspace + "_evil"
        os.makedirs(evil_workspace, exist_ok=True)

        evil_file = os.path.join(evil_workspace, "evil.txt")
        Path(evil_file).touch()

        # Doit être bloqué car hors workspace
        is_valid, msg = is_path_in_workspace(evil_file)
        assert not is_valid, "Fichier dans workspace similaire accepté à tort"

        # Cleanup
        import shutil

        shutil.rmtree(evil_workspace)


class TestSymlinkResolutionEdgeCases:
    """Tests pour edge cases de résolution symlinks"""

    def test_symlink_to_current_directory(self):
        """Symlink vers répertoire courant doit être géré"""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings.WORKSPACE_DIR = tmpdir

            # Créer symlink vers .
            self_link = os.path.join(tmpdir, "self")
            try:
                os.symlink(".", self_link)
            except OSError:
                pytest.skip("Cannot create symlinks")

            is_valid, msg = is_path_in_workspace(self_link)
            # Doit être accepté car résout vers workspace
            assert is_valid

    def test_broken_symlink_handled(self):
        """Symlink cassé doit être géré sans crash"""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings.WORKSPACE_DIR = tmpdir

            # Créer symlink vers fichier inexistant
            broken_link = os.path.join(tmpdir, "broken")
            try:
                os.symlink("/nonexistent/file", broken_link)
            except OSError:
                pytest.skip("Cannot create symlinks")

            # Ne doit pas crasher
            is_valid, msg = is_path_in_workspace(broken_link)
            # Doit être bloqué car pointe hors workspace
            assert not is_valid
