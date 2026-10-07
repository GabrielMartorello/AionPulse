// SPDX-License-Identifier: GPL-3.0-only
using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

class AionPulseLauncher
{
    [STAThread]
    static int Main(string[] args)
    {
        try
        {
            string folder = AppDomain.CurrentDomain.BaseDirectory;
            string python = Environment.GetEnvironmentVariable("AIONPULSE_PYTHON");
            if (String.IsNullOrWhiteSpace(python))
            {
                string environment = Path.Combine(folder, ".venv", "Scripts", "pythonw.exe");
                python = File.Exists(environment) ? environment : "pythonw.exe";
            }
            string script = Path.Combine(folder, "app.py");
            if (!File.Exists(script))
                throw new FileNotFoundException("O runtime ou os arquivos do AionPulse não foram encontrados.");
            var start = new ProcessStartInfo(python);
            start.Arguments = "\"" + script + "\" --capture --overlay";
            if (Array.IndexOf(args, "--diagnostic-state") >= 0)
                start.Arguments += " --diagnostic-state";
            if (Array.IndexOf(args, "--show-main") >= 0)
                start.Arguments += " --show-main";
            start.WorkingDirectory = folder;
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            start.WindowStyle = ProcessWindowStyle.Hidden;
            using (Process child = Process.Start(start))
            {
                child.WaitForExit();
                return child.ExitCode;
            }
        }
        catch (Exception error)
        {
            MessageBox.Show(error.Message, "AionPulse", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
