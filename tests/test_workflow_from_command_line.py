import unittest
import subprocess
import pytest


class TestWorkflowFromCommandLine(unittest.TestCase):
    @pytest.mark.order(1)
    def test_1_get_binary(self):
        result = subprocess.run(["python3", "../run_sims/get_latest_binary.py"], capture_output=True, text=True)
        if result.returncode:
            print(result.stderr)
        self.assertEqual(result.returncode, 0)  # Check if the script ran successfully
        self.assertIn("done", result.stdout.strip())

    @pytest.mark.order(2)
    def test_2_run_script(self):
        result = subprocess.run(["python3", "../run_sims/run_from_command_line.py",
                                 "-i", "emod_output/emod_exp_test.id", "-a", "test",
                                 "-p", "1", "-r", "30", "-t", "0.05", "0.1", "-m", "3", "-s", "1"], capture_output=True, text=True)
        if result.returncode:
            print(result.stderr)
        self.assertEqual(result.returncode, 0)  # Check if the script ran successfully
        self.assertIn("succeeded", result.stdout.strip())  # Check if the output matches the expected result

    @pytest.mark.order(3)
    def test_3_post_simulation_steps(self):
        result = subprocess.run(["python3", "../workflow/post_simulation_steps.py",
                                 "-i", "emod_output/emod_exp_test.id", "-o", "emod_output"], capture_output=True,
                                text=True)
        if result.returncode:
            print(result.stderr)
        self.assertEqual(result.returncode, 0)  # Check if the script ran successfully
        self.assertIn("total download time", result.stdout.strip())


if __name__ == '__main__':
    unittest.main()
