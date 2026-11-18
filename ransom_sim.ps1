# The message is hardcoded here using a PowerShell Here-String
$Message = @"
Test file for Ransomware
If you are seeing this, you have been hacked.
Pay up or else.
"@

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "SYSTEM LOCKED"
$form.WindowState = [System.Windows.Forms.FormWindowState]::Maximized
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.TopMost = $true
$form.BackColor = [System.Drawing.Color]::Black
$form.StartPosition = "CenterScreen"
$form.KeyPreview = $true

# LABEL (Text)
$label = New-Object System.Windows.Forms.Label
$label.Text = $Message
$label.ForeColor = [System.Drawing.Color]::Lime
$label.Font = New-Object System.Drawing.Font("Consolas", 26, [System.Drawing.FontStyle]::Bold)
$label.TextAlign = "MiddleCenter"
$label.Dock = [System.Windows.Forms.DockStyle]::Fill
$form.Controls.Add($label)

# BUTTON
$button = New-Object System.Windows.Forms.Button
$button.Text = "Pay Ransom"
$button.Font = New-Object System.Drawing.Font("Consolas", 20, [System.Drawing.FontStyle]::Bold)
$button.ForeColor = [System.Drawing.Color]::White
$button.BackColor = [System.Drawing.Color]::DarkRed
$button.FlatStyle = "Flat"
$button.Width = 320
$button.Height = 90
$button.Dock = [System.Drawing.DockStyle]::Bottom
$form.Controls.Add($button)
$button.BringToFront()

# "Pay Ransom" -> fake decrypt progress, then close cleanly
$button.Add_Click({
    $button.Enabled = $false
    $button.Text = "Decrypting..."
    for ($i = 0; $i -le 100; $i += 7) {
        $label.Text = "Decrypting your files... $i%"
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 120
    }
    $label.Text = "Simulation complete. Files were never touched."
    Start-Sleep -Milliseconds 800
    $form.Tag = "paid"
    $form.Close()
})

# Block X / Alt+F4 / Esc unless paid
$form.Add_FormClosing({
    param($sender, $e)
    if ($sender.Tag -ne "paid") {
        $e.Cancel = $true
        $sender.WindowState = [System.Windows.Forms.FormWindowState]::Maximized
        $sender.TopMost = $true
        $sender.Activate()
    }
})

$form.Add_KeyDown({
    param($sender, $e)
    if (($e.Alt -and $e.KeyCode -eq [System.Windows.Forms.Keys]::F4) -or $e.KeyCode -eq [System.Windows.Forms.Keys]::Escape) {
        $e.SuppressKeyPress = $true
    }
})

[System.Windows.Forms.Application]::Run($form)
