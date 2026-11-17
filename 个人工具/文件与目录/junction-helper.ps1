$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Linq;
using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class VerifiedMigrationJunction {
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern SafeFileHandle CreateFileW(string path, uint access, uint share, IntPtr security, uint creation, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool DeviceIoControl(SafeFileHandle handle, uint code, byte[] input, uint inputSize, IntPtr output, uint outputSize, out uint returned, IntPtr overlapped);
    static SafeFileHandle Open(string path) {
        var handle = CreateFileW(path, 0x40000000, 7, IntPtr.Zero, 3, 0x02200000, IntPtr.Zero);
        if (handle.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
        return handle;
    }
    public static void CheckWriteAccess(string path) { using(var handle = Open(path)) {} }
    public static void CreateInEmptyDirectory(string source, string destination) {
        source = Path.GetFullPath(source); destination = Path.GetFullPath(destination);
        bool approved =
            (source == @"C:\Users\Lenovo\Documents\Codex" && destination == @"E:\Documents\ChatGPT\Codex") ||
            (source == @"C:\Users\Lenovo\.codex\visualizations" && destination == @"E:\Documents\ChatGPT\可视化") ||
            (source == @"E:\Documents\ChatGPT\电脑调试\junction-test-source" && destination == @"E:\Documents\ChatGPT\电脑调试\junction-test-target");
        if(!approved) throw new InvalidOperationException("Path pair is outside the migration allowlist.");
        if(!Directory.Exists(destination) || !Directory.Exists(source)) throw new DirectoryNotFoundException();
        if((File.GetAttributes(source) & FileAttributes.ReparsePoint) != 0) throw new IOException("Source is already a link.");
        if(Directory.EnumerateFileSystemEntries(source).Any()) throw new IOException("Source directory is not empty.");
        var substitute = System.Text.Encoding.Unicode.GetBytes(@"\??\" + destination);
        var print = System.Text.Encoding.Unicode.GetBytes(destination);
        ushort dataLength = checked((ushort)(8 + substitute.Length + 2 + print.Length + 2));
        var buffer = new byte[8 + dataLength];
        Array.Copy(BitConverter.GetBytes(0xA0000003u), 0, buffer, 0, 4);
        Array.Copy(BitConverter.GetBytes(dataLength), 0, buffer, 4, 2);
        Array.Copy(BitConverter.GetBytes((ushort)substitute.Length), 0, buffer, 10, 2);
        Array.Copy(BitConverter.GetBytes((ushort)(substitute.Length + 2)), 0, buffer, 12, 2);
        Array.Copy(BitConverter.GetBytes((ushort)print.Length), 0, buffer, 14, 2);
        Array.Copy(substitute, 0, buffer, 16, substitute.Length);
        Array.Copy(print, 0, buffer, 16 + substitute.Length + 2, print.Length);
        using(var handle = Open(source)) {
            uint returned;
            if(!DeviceIoControl(handle, 0x000900A4, buffer, (uint)buffer.Length, IntPtr.Zero, 0, out returned, IntPtr.Zero))
                throw new Win32Exception(Marshal.GetLastWin32Error());
        }
    }
}
'@
