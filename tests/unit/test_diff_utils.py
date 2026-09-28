from pr_review_agent.tools.diff_utils import extract_changed_files

SAMPLE_DIFF = """diff --git a/src/foo.py b/src/foo.py
index abc123..def456 100644
--- a/src/foo.py
+++ b/src/foo.py
@@ -1,1 +1,2 @@
 print("hi")
+print("bye")
diff --git a/tests/test_foo.py b/tests/test_foo.py
new file mode 100644
--- /dev/null
+++ b/tests/test_foo.py
@@ -0,0 +1 @@
+def test_foo(): ...
diff --git a/old_file.py b/old_file.py
deleted file mode 100644
--- a/old_file.py
+++ /dev/null
@@ -1,1 +0,0 @@
-print("gone")
"""


def test_extract_changed_files_includes_added_and_modified():
    files = extract_changed_files(SAMPLE_DIFF)
    assert "src/foo.py" in files
    assert "tests/test_foo.py" in files


def test_extract_changed_files_excludes_deletions():
    files = extract_changed_files(SAMPLE_DIFF)
    assert "old_file.py" not in files
