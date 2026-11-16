/*
 * Intel ACPI Component Architecture
 * AML/ASL+ Disassembler version 20230628 (64-bit version)
 * Copyright (c) 2000 - 2023 Intel Corporation
 * 
 * Disassembling to symbolic ASL+ operators
 *
 * Disassembly of SSDT21.aml, Fri Sep 25 21:42:01 2026
 *
 * Original Table Header:
 *     Signature        "SSDT"
 *     Length           0x00001707 (5895)
 *     Revision         0x02
 *     Checksum         0xB3
 *     OEM ID           "AMD"
 *     OEM Table ID     "UPEPRPL "
 *     OEM Revision     0x00000001 (1)
 *     Compiler ID      "INTL"
 *     Compiler Version 0x20200717 (538969879)
 */
DefinitionBlock ("", "SSDT", 2, "AMD", "UPEPRPL ", 0x00000001)
{
    External (_SB_.ACDC.MONR, UnknownObj)
    External (_SB_.ACDC.RTAC, UnknownObj)
    External (_SB_.ACDC.YARR, UnknownObj)
    External (_SB_.AMW0.FMFG, IntObj)
    External (_SB_.INOU.CSTM, IntObj)
    External (_SB_.PC00.LPCB.EC0_.CSMS, IntObj)
    External (_SB_.PC00.LPCB.EC0_.LCSE, IntObj)
    External (_SB_.PC00.LPCB.EC0_.OCP1, IntObj)
    External (_SB_.PC00.LPCB.EC0_.OCP2, IntObj)
    External (_SB_.PC00.LPCB.EC0_.TB43, IntObj)
    External (_SB_.PCI0, DeviceObj)
    External (_SB_.PCI0.GPP6.SDCR, DeviceObj)
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
    External (M000, MethodObj)    // 1 Arguments
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
    External (M460, MethodObj)    // 7 Arguments
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

    Scope (\_SB.PCI0)
    {
        Name (_DEP, Package (0x01)  // _DEP: Dependencies
        {
            \_SB.PEP
        })
    }

    Scope (\_SB)
    {
        Device (PEP)
        {
            Name (_HID, "AMDI0008")  // _HID: Hardware ID
            Name (_CID, EisaId ("PNP0D80") /* Windows-compatible System Power Management Controller */)  // _CID: Compatible ID
            Name (_UID, One)  // _UID: Unique ID
            Name (PRMD, Zero)
            Name (DEV0, Package (0x03)
            {
                Zero, 
                0x31, 
                Package (0x31)
                {
                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C000", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C001", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C002", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C003", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C004", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C005", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C006", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C007", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C008", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C009", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C00A", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C00B", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C00C", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C00D", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C00E", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C00F", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C010", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C011", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C012", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C013", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C014", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C015", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C016", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C017", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C018", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C019", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C01A", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C01B", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C01C", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C01D", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C01E", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PLTF.C01F", 
                        One, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GPP0", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GPP2", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GPP3", 
                        0x02, 
                        One
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GPP3.WLAN", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GPP6.SDCR", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GPP5", 
                        0x02, 
                        One
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GPP5.GLAN", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GPP1.NVME", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GPP4.NVME", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GP17.VGA", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GP17.AZAL", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GP17.ACP", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GP17.HDAU", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GP17.XHC0", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GP17.XHC1", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.GP19.XHC2", 
                        Zero, 
                        0x03
                    }, 

                    Package (0x04)
                    {
                        One, 
                        "\\_SB.PCI0.I2CB", 
                        Zero, 
                        0x03
                    }
                }
            })
            Method (_STA, 0, NotSerialized)  // _STA: Status
            {
                Return (0x0F)
            }

            Method (_DSM, 4, Serialized)  // _DSM: Device-Specific Method
            {
                If ((Arg0 == ToUUID ("e3f32452-febc-43ce-9039-932122d37721") /* Unknown UUID */))
                {
                    Switch (ToInteger (Arg2))
                    {
                        Case (Zero)
                        {
                            Switch (ToInteger (Arg1))
                            {
                                Case (Zero)
                                {
                                    Return (Buffer (One)
                                    {
                                         0x03                                             // .
                                    })
                                }
                                Case (One)
                                {
                                    Return (Buffer (One)
                                    {
                                         0x03                                             // .
                                    })
                                }
                                Case (0x02)
                                {
                                    Return (Buffer (One)
                                    {
                                         0x3F                                             // ?
                                    })
                                }
                                Default
                                {
                                    Return (Buffer (One)
                                    {
                                         0x00                                             // .
                                    })
                                }

                            }
                        }
                        Case (One)
                        {
                            Return (DEV0) /* \_SB_.PEP_.DEV0 */
                        }
                        Case (0x02)
                        {
                            M000 (0x3E14)
                            Return (Zero)
                        }
                        Case (0x03)
                        {
                            M000 (0x3E15)
                            Return (Zero)
                        }
                        Case (0x04)
                        {
                            M000 (0x3E12)
                            Return (Zero)
                        }
                        Case (0x05)
                        {
                            M000 (0x3E13)
                            Return (Zero)
                        }
                        Default
                        {
                            Return (Zero)
                        }

                    }
                }
                ElseIf ((Arg0 == ToUUID ("11e00d56-ce64-47ce-837b-1f898f9aa461") /* Unknown UUID */))
                {
                    Name (TMPD, Zero)
                    Name (FFNT, Zero)
                    Mutex (PEPM, 0x00)
                    Switch (ToInteger (Arg2))
                    {
                        Case (Zero)
                        {
                            Switch (ToInteger (Arg1))
                            {
                                Case (Zero)
                                {
                                    Return (Buffer (0x02)
                                    {
                                         0xF9, 0x01                                       // ..
                                    })
                                }
                                Default
                                {
                                    Return (Buffer (One)
                                    {
                                         0x00                                             // .
                                    })
                                }

                            }
                        }
                        Case (0x03)
                        {
                            M000 (0x3E03)
                            \_SB.PCI0.SBRG.EC0.S0E1 = One
                            Return (Zero)
                        }
                        Case (0x04)
                        {
                            Local0 = \_SB.PCI0.SBRG.EC0.S0E1 /* External reference */
                            \_SB.PCI0.SBRG.EC0.S0E1 = Zero
                            If ((\_SB.ACDC.RTAC == 0x20))
                            {
                                \_SB.PCI0.SBRG.EC0.EYER = \_SB.ACDC.YARR /* External reference */
                                \_SB.PCI0.SBRG.EC0.EMON = \_SB.ACDC.MONR /* External reference */
                            }
                            Else
                            {
                                \_SB.PCI0.SBRG.EC0.EYER = Zero
                                \_SB.PCI0.SBRG.EC0.EMON = Zero
                            }

                            If (Local0)
                            {
                                Acquire (PEPM, 0x07D0)
                                If ((\_SB.PCI0.SBRG.EC0.OUTS == Zero))
                                {
                                    While (\_SB.PCI0.SBRG.EC0.INPS){}
                                    \_SB.PCI0.SBRG.EC0.CMD4 = 0xAA
                                    FFNT = 0x14
                                    While (!\_SB.PCI0.SBRG.EC0.OUTS)
                                    {
                                        FFNT -= One
                                        If ((FFNT == Zero))
                                        {
                                            Break
                                        }

                                        Sleep (0x32)
                                    }

                                    While (\_SB.PCI0.SBRG.EC0.OUTS)
                                    {
                                        TMPD = \_SB.PCI0.SBRG.EC0.CMD0 /* External reference */
                                    }
                                }

                                Release (PEPM)
                            }

                            M000 (0x3E04)
                            Acquire (PEPM, 0x07D0)
                            While (\_SB.PCI0.SBRG.EC0.OUTS)
                            {
                                TMPD = \_SB.PCI0.SBRG.EC0.CMD0 /* External reference */
                            }

                            Release (PEPM)
                            Return (Zero)
                        }
                        Case (0x05)
                        {
                            M000 (0x3E05)
                            Acquire (PEPM, 0x07D0)
                            While (\_SB.PCI0.SBRG.EC0.OUTS)
                            {
                                TMPD = \_SB.PCI0.SBRG.EC0.CMD0 /* External reference */
                            }

                            Release (PEPM)
                            Return (Zero)
                        }
                        Case (0x06)
                        {
                            M000 (0x3E06)
                            Acquire (PEPM, 0x07D0)
                            While (\_SB.PCI0.SBRG.EC0.OUTS)
                            {
                                TMPD = \_SB.PCI0.SBRG.EC0.CMD0 /* External reference */
                            }

                            Release (PEPM)
                            Return (Zero)
                        }
                        Case (0x07)
                        {
                            M000 (0x3E07)
                            Acquire (PEPM, 0x07D0)
                            While (\_SB.PCI0.SBRG.EC0.OUTS)
                            {
                                TMPD = \_SB.PCI0.SBRG.EC0.CMD0 /* External reference */
                            }

                            Release (PEPM)
                            \_SB.PCI0.SBRG.EC0.S0E3 = One
                            Return (Zero)
                        }
                        Case (0x08)
                        {
                            M000 (0x3E08)
                            Acquire (PEPM, 0x07D0)
                            While (\_SB.PCI0.SBRG.EC0.OUTS)
                            {
                                TMPD = \_SB.PCI0.SBRG.EC0.CMD0 /* External reference */
                            }

                            Release (PEPM)
                            \_SB.PCI0.SBRG.EC0.S0E3 = Zero
                            If (CondRefOf (\_SB.PCI0.GPP6.SDCR))
                            {
                                M460 ("    Notify (\\_SB.PCI0.GPP6.SDCR, 0x1)\n", Zero, Zero, Zero, Zero, Zero, Zero)
                                Notify (\_SB.PCI0.GPP6.SDCR, One) // Device Check
                            }

                            Return (Zero)
                        }
                        Default
                        {
                            Return (Zero)
                        }

                    }
                }
                Else
                {
                    Return (Buffer (One)
                    {
                         0x00                                             // .
                    })
                }
            }
        }
    }
}

