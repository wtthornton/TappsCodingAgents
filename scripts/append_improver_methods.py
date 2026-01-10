#!/usr/bin/env python3
"""Append Phase 7.1 methods to ImproverAgent."""

from pathlib import Path

NEW_METHODS = '''
    # ========================================================================
    # Phase 7.1: Auto-Apply Enhancement Methods
    # ========================================================================
    
    def _create_backup(self, file_path: str) -> Path | None:
        """
        Create backup of file before modifications.
        
        Phase 7.1: Auto-Apply Enhancement
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to backup file, or None if backup failed
            
        Backup Location:
            .tapps-agents/backups/<filename>.<timestamp>.backup
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.is_absolute():
                file_path_obj = self.project_root / file_path_obj
            
            if not file_path_obj.exists():
                logger.warning(f"Cannot backup non-existent file: {file_path}")
                return None
            
            # Create backup directory
            backup_dir = self.project_root / ".tapps-agents" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_filename = f"{file_path_obj.name}.{timestamp}.backup"
            backup_path = backup_dir / backup_filename
            
            # Copy file to backup location
            shutil.copy2(file_path_obj, backup_path)
            logger.info(f"Created backup: {backup_path}")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def _apply_improvements(
        self, file_path: str, improved_code: str
    ) -> dict[str, Any]:
        """
        Apply improved code to file.
        
        Phase 7.1: Auto-Apply Enhancement
        
        Args:
            file_path: Path to file to modify
            improved_code: Improved code content
            
        Returns:
            Dictionary with result status
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.is_absolute():
                file_path_obj = self.project_root / file_path_obj
            
            if not improved_code or not improved_code.strip():
                return {"success": False, "error": "Improved code is empty"}
            
            # Write improved code
            file_path_obj.write_text(improved_code, encoding="utf-8")
            logger.info(f"Applied improvements to: {file_path}")
            
            return {
                "success": True,
                "file": str(file_path_obj),
                "bytes_written": len(improved_code.encode("utf-8")),
            }
            
        except Exception as e:
            logger.error(f"Failed to apply improvements to {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_diff(
        self, original: str, improved: str, file_path: str = "file"
    ) -> dict[str, Any]:
        """
        Generate unified diff between original and improved code.
        
        Phase 7.1: Auto-Apply Enhancement
        
        Args:
            original: Original code content
            improved: Improved code content
            file_path: File path for diff header
            
        Returns:
            Dictionary with diff result
        """
        try:
            original_lines = original.splitlines(keepends=True)
            improved_lines = improved.splitlines(keepends=True)
            
            # Generate unified diff
            diff_lines = list(difflib.unified_diff(
                original_lines,
                improved_lines,
                fromfile=f"original/{file_path}",
                tofile=f"improved/{file_path}",
                lineterm="",
            ))
            
            unified_diff = "".join(diff_lines)
            
            # Calculate statistics
            lines_added = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
            lines_removed = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
            has_changes = bool(diff_lines)
            
            return DiffResult(
                unified_diff=unified_diff,
                lines_added=lines_added,
                lines_removed=lines_removed,
                has_changes=has_changes,
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Failed to generate diff: {e}")
            return DiffResult(
                unified_diff="",
                lines_added=0,
                lines_removed=0,
                has_changes=False,
            ).to_dict()
    
    async def _verify_changes(self, file_path: str) -> dict[str, Any]:
        """
        Run verification review after applying changes.
        
        Phase 7.1: Auto-Apply Enhancement
        
        Args:
            file_path: Path to modified file
            
        Returns:
            Dictionary with verification results
        """
        try:
            # Import reviewer agent for verification
            from ..reviewer.agent import ReviewerAgent
            
            reviewer = ReviewerAgent(config=self.config)
            await reviewer.activate(self.project_root, offline_mode=True)
            
            file_path_obj = Path(file_path)
            if not file_path_obj.is_absolute():
                file_path_obj = self.project_root / file_path_obj
            
            # Run review
            review_result = await reviewer.review_file(file_path_obj)
            
            # Extract score
            scores = review_result.get("scoring", {})
            overall_score = scores.get("overall_score", 0.0)
            
            return {
                "verified": True,
                "new_score": overall_score,
                "scores": scores,
                "review": review_result,
            }
            
        except Exception as e:
            logger.error(f"Failed to verify changes for {file_path}: {e}")
            return {
                "verified": False,
                "error": str(e),
            }
'''

def main():
    file_path = Path("tapps_agents/agents/improver/agent.py")
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
    
    content = file_path.read_text(encoding="utf-8")
    
    # Check if methods already exist
    if "_create_backup" in content and "def _create_backup" in content:
        print("Methods already exist in file")
        return
    
    # Append new methods
    if not content.endswith("\n"):
        content += "\n"
    
    content += NEW_METHODS
    
    file_path.write_text(content, encoding="utf-8")
    print(f"Added Phase 7.1 methods to {file_path}")
    print(f"New file size: {len(content)} characters")

if __name__ == "__main__":
    main()
