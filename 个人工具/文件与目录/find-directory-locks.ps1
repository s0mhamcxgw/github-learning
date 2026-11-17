$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Collections.Generic;
using Microsoft.Win32.SafeHandles;
public static class DirectoryLockDiagnostic {
    [DllImport("ntdll.dll")] static extern int NtQuerySystemInformation(int cls, IntPtr buf, int size, out int needed);
    [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool DuplicateHandle(IntPtr src, IntPtr value, IntPtr dest, out IntPtr copied, uint access, bool inherit, uint options);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll")] static extern uint GetFileType(IntPtr handle);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern uint GetFinalPathNameByHandleW(IntPtr handle, StringBuilder name, uint size, uint flags);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern SafeFileHandle CreateFileW(string path, uint access, uint share, IntPtr security, uint creation, uint flags, IntPtr template);
    [StructLayout(LayoutKind.Sequential)] struct Entry {
        public IntPtr Object; public UIntPtr Pid; public UIntPtr Handle;
        public uint Access; public ushort Trace; public ushort Type;
        public uint Attributes; public uint Reserved;
    }
    public static string[] Find() {
        const string root = @"C:\Users\Lenovo\Documents\Codex";
        var result = new List<string>(); var processes = new Dictionary<uint,IntPtr>();
        using(var probe = CreateFileW(root, 0, 7, IntPtr.Zero, 3, 0x02000000, IntPtr.Zero)) {
            if(probe.IsInvalid) throw new Exception("Unable to open directory metadata.");
            int size=4*1024*1024, needed; IntPtr buf=IntPtr.Zero;
            try {
                while(true) {
                    buf=Marshal.AllocHGlobal(size);
                    int status=NtQuerySystemInformation(64,buf,size,out needed);
                    if(status==0) break;
                    Marshal.FreeHGlobal(buf); buf=IntPtr.Zero;
                    if(status!=unchecked((int)0xC0000004)) throw new Exception("Handle query failed.");
                    size=Math.Max(size*2,needed+1024*1024);
                }
                long count=Marshal.ReadInt64(buf); int stride=Marshal.SizeOf<Entry>();
                uint self=(uint)Process.GetCurrentProcess().Id; ushort fileType=0;
                for(long i=0;i<count;i++) {
                    var e=Marshal.PtrToStructure<Entry>(IntPtr.Add(buf,checked(16+(int)i*stride)));
                    if(e.Pid.ToUInt64()==self && e.Handle.ToUInt64()==(ulong)probe.DangerousGetHandle().ToInt64()) {fileType=e.Type;break;}
                }
                if(fileType==0) throw new Exception("Unable to determine file handle type.");
                for(long i=0;i<count;i++) {
                    var e=Marshal.PtrToStructure<Entry>(IntPtr.Add(buf,checked(16+(int)i*stride)));
                    uint pid=(uint)e.Pid.ToUInt64(); if(e.Type!=fileType || pid==self) continue;
                    IntPtr process;
                    if(!processes.TryGetValue(pid,out process)) {process=OpenProcess(0x40,false,pid);processes[pid]=process;}
                    if(process==IntPtr.Zero) continue;
                    IntPtr copied;
                    if(!DuplicateHandle(process,new IntPtr((long)e.Handle.ToUInt64()),GetCurrentProcess(),out copied,0,false,2)) continue;
                    try {
                        if(GetFileType(copied)!=1) continue;
                        var name=new StringBuilder(2048);
                        uint length=GetFinalPathNameByHandleW(copied,name,2048,0);
                        if(length==0 || length>=2048) continue;
                        string path=name.ToString(); if(path.StartsWith(@"\\?\")) path=path.Substring(4);
                        if(path.Equals(root,StringComparison.OrdinalIgnoreCase) || path.StartsWith(root+"\\",StringComparison.OrdinalIgnoreCase)) {
                            string processName; try{processName=Process.GetProcessById((int)pid).ProcessName;}catch{processName="exited";}
                            result.Add(pid+" | "+processName+" | "+path);
                        }
                    } finally {CloseHandle(copied);}
                }
            } finally {
                if(buf!=IntPtr.Zero) Marshal.FreeHGlobal(buf);
                foreach(var p in processes.Values) if(p!=IntPtr.Zero) CloseHandle(p);
            }
        }
        return result.ToArray();
    }
}
'@
[DirectoryLockDiagnostic]::Find() | Sort-Object -Unique
