Start-Sleep -Seconds 4

Add-Type @"
using System.Runtime.InteropServices;
public class W {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(System.IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(System.IntPtr h, int n);
}
"@

$e = Get-Process msedge -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if ($e) {
    [W]::ShowWindow($e.MainWindowHandle, 3)
    [W]::SetForegroundWindow($e.MainWindowHandle)
}

Start-Sleep -Seconds 2

Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$s = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap($s.Width, $s.Height)
$g   = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($s.Location, [System.Drawing.Point]::Empty, $s.Size)
$bmp.Save("C:\Users\leedh\OneDrive\바탕 화면\workspace\project\screen_final.png")
$g.Dispose(); $bmp.Dispose()
