/*
 * Intel ACPI Component Architecture
 * AML/ASL+ Disassembler version 20230628 (64-bit version)
 * Copyright (c) 2000 - 2023 Intel Corporation
 * 
 * Disassembling to symbolic ASL+ operators
 *
 * Disassembly of SSDT22.aml, Fri Sep 25 21:42:01 2026
 *
 * Original Table Header:
 *     Signature        "SSDT"
 *     Length           0x00000E76 (3702)
 *     Revision         0x02
 *     Checksum         0x1B
 *     OEM ID           "AMD"
 *     OEM Table ID     "GPPRPL  "
 *     OEM Revision     0x00000001 (1)
 *     Compiler ID      "INTL"
 *     Compiler Version 0x20200717 (538969879)
 */
DefinitionBlock ("", "SSDT", 2, "AMD", "GPPRPL  ", 0x00000001)
{
    External (_SB_.AMW0.FMFG, IntObj)
    External (_SB_.INOU.CSTM, IntObj)
    External (_SB_.PC00.LPCB.EC0_.CSMS, IntObj)
    External (_SB_.PC00.LPCB.EC0_.LCSE, IntObj)
    External (_SB_.PC00.LPCB.EC0_.OCP1, IntObj)
    External (_SB_.PC00.LPCB.EC0_.OCP2, IntObj)
    External (_SB_.PC00.LPCB.EC0_.TB43, IntObj)
    External (_SB_.PCI0.GPP3, DeviceObj)
    External (_SB_.PCI0.GPP3.WLAN, DeviceObj)
    External (_SB_.PCI0.GPP5, DeviceObj)
    External (_SB_.PCI0.GPP5.GLAN, DeviceObj)
    External (_SB_.PCI0.GPP6, DeviceObj)
    External (_SB_.PCI0.SBRG.EC0_.ACIC, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.ADPT, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.APL1, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.APL4, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.APTC, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.APTN, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.BFLG, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.BLLV, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.BLSC, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.BPST, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CFLG, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CGCT, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CMD0, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CMD2, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CMD4, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CMD6, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CMDH, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CMDL, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CPTM, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CPUA, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CTWA, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CUME, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DBAP, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DBD1, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DBD2, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DBEN, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DBST, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DC0C, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DRDY, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.EMON, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.EYER, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.FFAN, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.GC6S, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.GFID, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.HDAT, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.IGPU, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.INPS, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.LDAT, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.OCPL, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.OUTS, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.S0E1, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.S0E3, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.SDAN, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.TBME, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.TC1C, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.TC2C, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.THOT, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.TPID, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.UFME, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.VGAT, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.WFLG, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.WHMS, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.WMS0, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.XHPP, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.XIF1, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.XIF4, IntObj)
    External (AUPT, IntObj)
    External (CL01, IntObj)
    External (CL02, IntObj)
    External (CL03, IntObj)
    External (CL04, IntObj)
    External (CLSP, IntObj)
    External (DDSS, IntObj)
    External (DPMD, IntObj)
    External (ECON, IntObj)
    External (G2OC, IntObj)
    External (G2OF, IntObj)
    External (G2OW, IntObj)
    External (G2VC, IntObj)
    External (G2VF, IntObj)
    External (G2VW, IntObj)
    External (G5OC, IntObj)
    External (G5OF, IntObj)
    External (G5OW, IntObj)
    External (G5VC, IntObj)
    External (G5VF, IntObj)
    External (G5VW, IntObj)
    External (G6VC, IntObj)
    External (G6VF, IntObj)
    External (G6VW, IntObj)
    External (M037, DeviceObj)
    External (M046, IntObj)
    External (M050, DeviceObj)
    External (M051, DeviceObj)
    External (M052, DeviceObj)
    External (M053, DeviceObj)
    External (M054, DeviceObj)
    External (M055, DeviceObj)
    External (M056, DeviceObj)
    External (M057, DeviceObj)
    External (M058, DeviceObj)
    External (M059, DeviceObj)
    External (M062, DeviceObj)
    External (M068, DeviceObj)
    External (M069, DeviceObj)
    External (M070, DeviceObj)
    External (M071, DeviceObj)
    External (M072, DeviceObj)
    External (M074, DeviceObj)
    External (M075, DeviceObj)
    External (M076, DeviceObj)
    External (M077, DeviceObj)
    External (M078, DeviceObj)
    External (M079, DeviceObj)
    External (M080, DeviceObj)
    External (M081, DeviceObj)
    External (M082, FieldUnitObj)
    External (M083, FieldUnitObj)
    External (M084, FieldUnitObj)
    External (M085, FieldUnitObj)
    External (M086, FieldUnitObj)
    External (M087, FieldUnitObj)
    External (M088, FieldUnitObj)
    External (M089, FieldUnitObj)
    External (M090, FieldUnitObj)
    External (M091, FieldUnitObj)
    External (M092, FieldUnitObj)
    External (M093, FieldUnitObj)
    External (M094, FieldUnitObj)
    External (M095, FieldUnitObj)
    External (M096, FieldUnitObj)
    External (M097, FieldUnitObj)
    External (M098, FieldUnitObj)
    External (M099, FieldUnitObj)
    External (M100, FieldUnitObj)
    External (M101, FieldUnitObj)
    External (M102, FieldUnitObj)
    External (M103, FieldUnitObj)
    External (M104, FieldUnitObj)
    External (M105, FieldUnitObj)
    External (M106, FieldUnitObj)
    External (M107, FieldUnitObj)
    External (M108, FieldUnitObj)
    External (M109, FieldUnitObj)
    External (M110, FieldUnitObj)
    External (M115, BuffObj)
    External (M116, BuffFieldObj)
    External (M117, BuffFieldObj)
    External (M118, BuffFieldObj)
    External (M119, BuffFieldObj)
    External (M120, BuffFieldObj)
    External (M122, FieldUnitObj)
    External (M127, DeviceObj)
    External (M128, FieldUnitObj)
    External (M131, FieldUnitObj)
    External (M132, FieldUnitObj)
    External (M133, FieldUnitObj)
    External (M134, FieldUnitObj)
    External (M135, FieldUnitObj)
    External (M136, FieldUnitObj)
    External (M220, FieldUnitObj)
    External (M221, FieldUnitObj)
    External (M226, FieldUnitObj)
    External (M227, DeviceObj)
    External (M229, FieldUnitObj)
    External (M231, FieldUnitObj)
    External (M233, FieldUnitObj)
    External (M235, FieldUnitObj)
    External (M23A, FieldUnitObj)
    External (M251, FieldUnitObj)
    External (M280, FieldUnitObj)
    External (M290, FieldUnitObj)
    External (M29A, FieldUnitObj)
    External (M310, FieldUnitObj)
    External (M31C, FieldUnitObj)
    External (M320, FieldUnitObj)
    External (M321, FieldUnitObj)
    External (M322, FieldUnitObj)
    External (M323, FieldUnitObj)
    External (M324, FieldUnitObj)
    External (M325, FieldUnitObj)
    External (M326, FieldUnitObj)
    External (M327, FieldUnitObj)
    External (M328, FieldUnitObj)
    External (M329, DeviceObj)
    External (M32A, DeviceObj)
    External (M32B, DeviceObj)
    External (M330, DeviceObj)
    External (M331, FieldUnitObj)
    External (M378, FieldUnitObj)
    External (M379, FieldUnitObj)
    External (M380, FieldUnitObj)
    External (M381, FieldUnitObj)
    External (M382, FieldUnitObj)
    External (M383, FieldUnitObj)
    External (M384, FieldUnitObj)
    External (M385, FieldUnitObj)
    External (M386, FieldUnitObj)
    External (M387, FieldUnitObj)
    External (M388, FieldUnitObj)
    External (M389, FieldUnitObj)
    External (M390, FieldUnitObj)
    External (M391, FieldUnitObj)
    External (M392, FieldUnitObj)
    External (M404, BuffObj)
    External (M408, MutexObj)
    External (M414, FieldUnitObj)
    External (M444, FieldUnitObj)
    External (M449, FieldUnitObj)
    External (M453, FieldUnitObj)
    External (M454, FieldUnitObj)
    External (M455, FieldUnitObj)
    External (M456, FieldUnitObj)
    External (M457, FieldUnitObj)
    External (M4C0, FieldUnitObj)
    External (M4F0, FieldUnitObj)
    External (M610, FieldUnitObj)
    External (M620, FieldUnitObj)
    External (M631, FieldUnitObj)
    External (MOID, IntObj)
    External (PEDD, UnknownObj)
    External (PMID, IntObj)
    External (PNSZ, IntObj)
    External (PPID, IntObj)
    External (S24G, IntObj)
    External (S5G1, IntObj)
    External (S5G2, IntObj)
    External (S5G3, IntObj)
    External (S5G4, IntObj)
    External (S6G1, IntObj)
    External (S6G2, IntObj)
    External (S6G3, IntObj)
    External (S6G4, IntObj)
    External (S6G5, IntObj)
    External (S6G6, IntObj)
    External (SARS, IntObj)
    External (UHBS, UnknownObj)
    External (WOL5, IntObj)

    Name (DSEN, 0x01)
    Name (DSI1, 0x5A5A5A5A)
    Scope (\_SB.PCI0.GPP3)
    {
        Name (_S0W, Zero)  // _S0W: S0 Device Wake State
    }

    Scope (\_SB.PCI0.GPP3.WLAN)
    {
        Method (_S0W, 0, NotSerialized)  // _S0W: S0 Device Wake State
        {
            Return (0x03)
        }

        OperationRegion (RPXX, PCI_Config, Zero, 0x10)
        Field (RPXX, DWordAcc, NoLock, Preserve)
        {
            DVID,   32
        }

        If (((DVID & 0xFFFF) == 0x14C3))
        {
            OperationRegion (FLDR, PCI_Config, 0x84, 0x08)
            Field (FLDR, DWordAcc, NoLock, Preserve)
            {
                DCAP,   32, 
                DCTR,   32
            }
        }
        Else
        {
            OperationRegion (FLDI, PCI_Config, 0x44, 0x08)
            Field (FLDI, DWordAcc, NoLock, Preserve)
            {
                DCAI,   32, 
                DCTI,   32
            }
        }

        PowerResource (PWFR, 0x05, 0x0000)
        {
            Method (_RST, 0, NotSerialized)  // _RST: Device Reset
            {
                If (((DVID & 0xFFFF) == 0x14C3))
                {
                    If ((DCAP & 0x10000000))
                    {
                        Local0 = DCTR /* \_SB_.PCI0.GPP3.WLAN.DCTR */
                        Local0 |= 0x8000
                        DCTR = Local0
                    }
                }
                ElseIf ((DCAI & 0x10000000))
                {
                    Local0 = DCTI /* \_SB_.PCI0.GPP3.WLAN.DCTI */
                    Local0 |= 0x8000
                    DCTI = Local0
                }
            }

            Method (_STA, 0, NotSerialized)  // _STA: Status
            {
                Return (0x0F)
            }

            Method (_ON, 0, NotSerialized)  // _ON_: Power On
            {
            }

            Method (_OFF, 0, NotSerialized)  // _OFF: Power Off
            {
            }
        }

        Method (_PRR, 0, NotSerialized)  // _PRR: Power Resource for Reset
        {
            Return (Package (0x01)
            {
                PWFR
            })
        }
    }

    Scope (\_SB.PCI0.GPP6)
    {
        PowerResource (PWR1, 0x00, 0x0000)
        {
            Name (PWRS, One)
            Method (_STA, 0, NotSerialized)  // _STA: Status
            {
                Return (PWRS) /* \_SB_.PCI0.GPP6.PWR1.PWRS */
            }

            Method (_ON, 0, NotSerialized)  // _ON_: Power On
            {
                PWRS = One
            }

            Method (_OFF, 0, NotSerialized)  // _OFF: Power Off
            {
                PWRS = Zero
            }
        }

        Name (_S0W, 0x04)  // _S0W: S0 Device Wake State
        Name (_PR0, Package (0x01)  // _PR0: Power Resources for D0
        {
            PWR1
        })
        Name (_PR2, Package (0x01)  // _PR2: Power Resources for D2
        {
            PWR1
        })
        Name (_PR3, Package (0x01)  // _PR3: Power Resources for D3hot
        {
            PWR1
        })
    }

    Scope (\_SB.PCI0.GPP5)
    {
        Name (_S0W, Zero)  // _S0W: S0 Device Wake State
    }

    Scope (\_SB.PCI0.GPP5.GLAN)
    {
        Method (_S0W, 0, NotSerialized)  // _S0W: S0 Device Wake State
        {
            Return (0x03)
        }

        Method (_PRW, 0, NotSerialized)  // _PRW: Power Resources for Wake
        {
            If ((WOL5 == One))
            {
                Return (Package (0x02)
                {
                    0x0E, 
                    0x04
                })
            }
            Else
            {
                Return (Package (0x02)
                {
                    0x0E, 
                    Zero
                })
            }
        }
    }
}

