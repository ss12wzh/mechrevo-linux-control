/*
 * Intel ACPI Component Architecture
 * AML/ASL+ Disassembler version 20230628 (64-bit version)
 * Copyright (c) 2000 - 2023 Intel Corporation
 * 
 * Disassembling to symbolic ASL+ operators
 *
 * Disassembly of SSDT10.aml, Fri Sep 25 21:42:00 2026
 *
 * Original Table Header:
 *     Signature        "SSDT"
 *     Length           0x0000168B (5771)
 *     Revision         0x02
 *     Checksum         0x32
 *     OEM ID           "AMD"
 *     OEM Table ID     "NVME    "
 *     OEM Revision     0x00000001 (1)
 *     Compiler ID      "INTL"
 *     Compiler Version 0x20200717 (538969879)
 */
DefinitionBlock ("", "SSDT", 2, "AMD", "NVME    ", 0x00000001)
{
    External (_SB_.AMW0.FMFG, IntObj)
    External (_SB_.INOU.CSTM, IntObj)
    External (_SB_.PC00.LPCB.EC0_.CSMS, IntObj)
    External (_SB_.PC00.LPCB.EC0_.LCSE, IntObj)
    External (_SB_.PC00.LPCB.EC0_.OCP1, IntObj)
    External (_SB_.PC00.LPCB.EC0_.OCP2, IntObj)
    External (_SB_.PC00.LPCB.EC0_.TB43, IntObj)
    External (_SB_.PCI0.GPP4, DeviceObj)
    External (_SB_.PCI0.GPP4._ADR, IntObj)
    External (_SB_.PCI0.RPCF, MethodObj)    // 0 Arguments
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
    External (_SB_.PCI0.SPCF, MethodObj)    // 0 Arguments
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
    External (M009, MethodObj)    // 1 Arguments
    External (M010, MethodObj)    // 2 Arguments
    External (M017, MethodObj)    // 6 Arguments
    External (M019, MethodObj)    // 4 Arguments
    External (M020, MethodObj)    // 5 Arguments
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
    External (M232, MethodObj)    // 3 Arguments
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
    External (M472, MethodObj)    // 4 Arguments
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

    Scope (\_SB.PCI0.GPP4)
    {
        Name (WD3C, Zero)
        Name (NBRI, 0x5A)
        Name (NBAR, 0x5A)
        Name (NCMD, 0x5A)
        Name (PXDC, 0x5A)
        Name (PXLC, 0x5A)
        Name (PXD2, 0x5A)
        Name (ASMI, 0xB2)
        Name (LCR1, 0x5A5A5A5A)
        Name (LCR2, 0x5A5A5A5A)
        Name (D3PK, Package (0x07)
        {
            Package (0x02)
            {
                "D3 Enabled", 
                Zero
            }, 

            Package (0x02)
            {
                "Reset Pin", 
                0x00000000
            }, 

            Package (0x02)
            {
                "Power Pin", 
                0x00000000
            }, 

            Package (0x02)
            {
                "Clk Req Mask", 
                0x00000000
            }, 

            Package (0x02)
            {
                "Tpvperl", 
                0x0032
            }, 

            Package (0x02)
            {
                "Trst-cfg", 
                0x0000
            }, 

            Package (0x05)
            {
                "APM SMI", 
                0x02, 
                0xD1, 
                0xD8, 
                0x5A
            }
        })
        OperationRegion (PSMI, SystemIO, ASMI, 0x02)
        Field (PSMI, AnyAcc, NoLock, Preserve)
        {
            ASMO,   8
        }

        OperationRegion (PMXX, SystemMemory, 0xFED80300, 0x0100)
        Field (PMXX, AnyAcc, NoLock, Preserve)
        {
            Offset (0x78), 
                ,   20, 
            SI3V,   1
        }

        Method (PWEN, 0, NotSerialized)
        {
            M460 ("PLA-ASL-_SB.PCI0.GPP4.PWEN\n", Zero, Zero, Zero, Zero, Zero, Zero)
            OperationRegion (VAMN, SystemMemory, 0xFED80E00, 0x04)
            Field (VAMN, ByteAcc, NoLock, Preserve)
            {
                CLKR,   32
            }

            If (CondRefOf (\_SB.PCI0.GPP4._ADR))
            {
                Name (ADDR, Buffer (0x04)
                {
                     0x00                                             // .
                })
                CreateByteField (ADDR, Zero, PFUN)
                CreateByteField (ADDR, 0x02, PDEV)
                ADDR = \_SB.PCI0.GPP4._ADR /* External reference */
            }

            Local0 = DerefOf (DerefOf (D3PK [One]) [One])
            Local2 = M009 (Local0)
            Local1 = DerefOf (DerefOf (D3PK [0x02]) [One])
            Local3 = M009 (Local1)
            Local6 = CLKR /* \_SB_.PCI0.GPP4.PWEN.CLKR */
            If (((Local2 == Zero) && (Local3 == Zero)))
            {
                WD3C = One
                M020 (Zero, PDEV, PFUN, 0x88, LCR2)
                M020 (Zero, PDEV, PFUN, 0x68, LCR1)
                Local4 = DerefOf (DerefOf (D3PK [0x03]) [One])
                CLKR &= Local4
                M010 (Local1, One)
                CLKR = Local6
                Local4 = DerefOf (DerefOf (D3PK [0x04]) [One])
                If ((Local4 != Zero))
                {
                    Sleep (Local4)
                }
                Else
                {
                    Sleep (0x64)
                }

                M472 (Zero, PDEV, PFUN, Zero)
                M010 (Local0, One)
                Local1 = Zero
                Local2 = 0x2775
                While ((((Local1 & 0x28) != 0x20) && (Local2 > Zero)))
                {
                    Local1 = M017 (Zero, PDEV, PFUN, 0x6B, Zero, 0x08)
                    Local2 = (Local2 - One)
                    Stall (0x63)
                }

                Local4 = DerefOf (DerefOf (D3PK [0x05]) [One])
                If ((Local4 != Zero))
                {
                    Sleep (Local4)
                }

                Local0 = M019 (Zero, PDEV, PFUN, 0x18)
                Local1 = ((Local0 & 0xFF00) >> 0x08)
                Local1 = M019 (Local1, Zero, Zero, Zero)
            }
        }

        Method (GPCG, 3, Serialized)
        {
            M460 ("PLA-ASL-_SB.PCI0.GPP4.GPCG Bus = 0x%X Dev = 0x%X Fun = 0x%X\n", Arg0, Arg1, Arg2, Zero, Zero, Zero)
            Local0 = Zero
            Local1 = M017 (Arg0, Arg1, Arg2, 0x34, Zero, 0x08)
            While ((Local1 != Zero))
            {
                Local2 = M017 (Arg0, Arg1, Arg2, Local1, Zero, 0x08)
                If (((Local2 == Zero) || (Local2 == 0xFF)))
                {
                    Break
                }

                If ((Local2 == 0x10))
                {
                    Local0 = Local1
                    Break
                }

                Local1 = M017 (Arg0, Arg1, Arg2, (Local1 + One), Zero, 0x08)
            }

            M460 ("PLA-ASL-_SB.PCI0.GPP4.GPCG Bus = 0x%X Dev = 0x%X Fun = 0x%X PCIe Cap Offset = 0x%X\n", Arg0, Arg1, Arg2, Local0, Zero, Zero)
            Return (Local0)
        }

        Method (RPCF, 0, NotSerialized)
        {
            M460 ("PLA-ASL-_SB.PCI0.GPP4.RPCF NBRI=0x%X\n", NBRI, Zero, Zero, Zero, Zero, Zero)
            If (CondRefOf (\_SB.PCI0.GPP4._ADR))
            {
                Local1 = GPCG (NBRI, Zero, Zero)
                M460 ("PLA-ASL-_SB.PCI0.GPP4.RPCF PXDC = 0x%X PXLC = 0x%X PXD2 = 0x%X NBAR = 0x%X NCMD = 0x%X\n", PXDC, PXLC, PXD2, NBAR, NCMD, Zero)
                M020 (NBRI, Zero, Zero, (Local1 + 0x08), PXDC)
                M020 (NBRI, Zero, Zero, (Local1 + 0x10), (PXLC & 0xFFFFFEFC))
                M020 (NBRI, Zero, Zero, (Local1 + 0x28), PXD2)
                M020 (NBRI, Zero, Zero, 0x10, NBAR)
                Local2 = (NCMD & 0xFFFFFBFF)
                M020 (NBRI, Zero, Zero, 0x04, (Local2 | 0x06))
            }
        }

        Method (SPCF, 0, NotSerialized)
        {
            M460 ("PLA-ASL-_SB.PCI0.GPP4.SPCF\n", Zero, Zero, Zero, Zero, Zero, Zero)
            If (CondRefOf (\_SB.PCI0.GPP4._ADR))
            {
                Name (ADDR, Buffer (0x04)
                {
                     0x00                                             // .
                })
                CreateByteField (ADDR, Zero, PFUN)
                CreateByteField (ADDR, 0x02, PDEV)
                ADDR = \_SB.PCI0.GPP4._ADR /* External reference */
                M460 ("PLA-ASL-_SB.PCI0.GPP4.SPCF Dev = 0x%X Func = 0x%X\n", PDEV, PFUN, Zero, Zero, Zero, Zero)
                Local0 = M019 (Zero, PDEV, PFUN, 0x18)
                NBRI = ((Local0 & 0xFF00) >> 0x08)
                NCMD = M019 (NBRI, Zero, Zero, 0x04)
                NBAR = M019 (NBRI, Zero, Zero, 0x10)
                Local1 = GPCG (NBRI, Zero, Zero)
                PXDC = M019 (NBRI, Zero, Zero, (Local1 + 0x08))
                PXLC = M019 (NBRI, Zero, Zero, (Local1 + 0x10))
                PXD2 = M019 (NBRI, Zero, Zero, (Local1 + 0x28))
                M460 ("PLA-ASL-_SB.PCI0.GPP4.RPCF NBRI = 0x%X NCMD = 0x%X NBAR = 0x%X \n", NBRI, NCMD, NBAR, Zero, Zero, Zero)
                M460 ("PLA-ASL-_SB.PCI0.GPP4.RPCF PXDC = 0x%X PXLC = 0x%X PXD2 = 0x%X \n", PXDC, PXLC, PXD2, Zero, Zero, Zero)
                LCR1 = M019 (Zero, PDEV, PFUN, 0x68)
                M460 ("PLA-ASL-_SB.PCI0.GPP4.PWDI.LCR1 : %x\n", LCR1, Zero, Zero, Zero, Zero, Zero)
                LCR2 = M019 (Zero, PDEV, PFUN, 0x88)
                M460 ("PLA-ASL-_SB.PCI0.GPP4.PWDI.LCR2 : %x\n", LCR2, Zero, Zero, Zero, Zero, Zero)
            }
        }

        PowerResource (P0NV, 0x00, 0x0000)
        {
            Name (D0NV, One)
            Method (_STA, 0, NotSerialized)  // _STA: Status
            {
                M000 (0x30AA)
                M460 ("PLA-ASL-\\_SB.PCI0.GPP4.P0NV._STA\n", Zero, Zero, Zero, Zero, Zero, Zero)
                Return (D0NV) /* \_SB_.PCI0.GPP4.P0NV.D0NV */
            }

            Method (_ON, 0, NotSerialized)  // _ON_: Power On
            {
                M000 (0x30D0)
                M460 ("PLA-ASL-\\_SB.PCI0.GPP4.P0NV._ON\n", Zero, Zero, Zero, Zero, Zero, Zero)
                If ((\_SB.PCI0.SBRG.EC0.S0E3 == One))
                {
                    RPCF ()
                    If (CondRefOf (\_SB.PCI0.RPCF))
                    {
                        \_SB.PCI0.RPCF ()
                    }

                    M232 (0xD8, Zero, Zero)
                }

                D0NV = One
                M000 (0x30D1)
            }

            Method (_OFF, 0, NotSerialized)  // _OFF: Power Off
            {
                M000 (0x30D3)
                M460 ("PLA-ASL-\\_SB.PCI0.GPP4.P0NV._OFF\n", Zero, Zero, Zero, Zero, Zero, Zero)
                SPCF ()
                If (CondRefOf (\_SB.PCI0.SPCF))
                {
                    \_SB.PCI0.SPCF ()
                }

                D0NV = Zero
                M000 (0x30D5)
            }
        }

        Device (NVME)
        {
            Name (_ADR, Zero)  // _ADR: Address
            Name (_S0W, 0x03)  // _S0W: S0 Device Wake State
            Name (_PR0, Package (0x01)  // _PR0: Power Resources for D0
            {
                P0NV
            })
            Name (_PR2, Package (0x01)  // _PR2: Power Resources for D2
            {
                P0NV
            })
            Name (_PR3, Package (0x01)  // _PR3: Power Resources for D3hot
            {
                P0NV
            })
            Method (_PS0, 0, NotSerialized)  // _PS0: Power State 0
            {
                M000 (0x3050)
                M460 ("PLA-ASL-\\_SB.PCI0.GPP4.NVME._PS0\n", Zero, Zero, Zero, Zero, Zero, Zero)
            }

            Method (_PS3, 0, NotSerialized)  // _PS3: Power State 3
            {
                M000 (0x3053)
                M460 ("PLA-ASL-\\_SB.PCI0.GPP4.NVME._PS3\n", Zero, Zero, Zero, Zero, Zero, Zero)
            }

            Name (_DSD, Package (0x02)  // _DSD: Device-Specific Data
            {
                ToUUID ("5025030f-842f-4ab4-a561-99a5189762d0") /* Unknown UUID */, 
                Package (0x01)
                {
                    Package (0x02)
                    {
                        "StorageD3Enable", 
                        One
                    }
                }
            })
        }
    }
}

