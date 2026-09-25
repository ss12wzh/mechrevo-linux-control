/*
 * Intel ACPI Component Architecture
 * AML/ASL+ Disassembler version 20230628 (64-bit version)
 * Copyright (c) 2000 - 2023 Intel Corporation
 * 
 * Disassembling to symbolic ASL+ operators
 *
 * Disassembly of SSDT15.aml, Fri Sep 25 21:42:00 2026
 *
 * Original Table Header:
 *     Signature        "SSDT"
 *     Length           0x000018A5 (6309)
 *     Revision         0x02
 *     Checksum         0x74
 *     OEM ID           "AMD"
 *     OEM Table ID     "CPMUCSI"
 *     OEM Revision     0x00000001 (1)
 *     Compiler ID      "INTL"
 *     Compiler Version 0x20200717 (538969879)
 */
DefinitionBlock ("", "SSDT", 2, "AMD", "CPMUCSI", 0x00000001)
{
    External (_SB_.AMW0.FMFG, IntObj)
    External (_SB_.INOU.CSTM, IntObj)
    External (_SB_.PC00.LPCB.EC0_.CSMS, IntObj)
    External (_SB_.PC00.LPCB.EC0_.LCSE, IntObj)
    External (_SB_.PC00.LPCB.EC0_.OCP1, IntObj)
    External (_SB_.PC00.LPCB.EC0_.OCP2, IntObj)
    External (_SB_.PC00.LPCB.EC0_.TB43, IntObj)
    External (_SB_.PCI0.SBRG.EC0_, UnknownObj)
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
    External (_SB_.PCI0.SBRG.EC0_.CCI0, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CCI1, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CCI2, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CCI3, IntObj)
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
    External (_SB_.PCI0.SBRG.EC0_.CTL0, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CTL1, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CTL2, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CTL3, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CTL4, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CTL5, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CTL6, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CTL7, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CTWA, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.CUME, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DBAP, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DBD1, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DBD2, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DBEN, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DBST, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DC0C, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.DRDY, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.ECMD, MethodObj)    // 1 Arguments
    External (_SB_.PCI0.SBRG.EC0_.EMON, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.EYER, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.FFAN, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.GC6S, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.GFID, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.HDAT, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.IGPU, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.INPS, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.LDAT, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGI0, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGI1, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGI2, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGI3, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGI4, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGI5, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGI6, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGI7, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGI8, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGI9, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGIA, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGIB, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGIC, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGID, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGIE, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGIF, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGO0, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGO1, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGO2, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGO3, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGO4, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGO5, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGO6, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGO7, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGO8, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGO9, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGOA, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGOB, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGOC, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGOD, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGOE, IntObj)
    External (_SB_.PCI0.SBRG.EC0_.MGOF, IntObj)
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
    External (M013, MethodObj)    // 4 Arguments
    External (M037, DeviceObj)
    External (M046, IntObj)
    External (M049, MethodObj)    // 2 Arguments
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

    Scope (\_SB)
    {
        Device (UBTC)
        {
            Name (_HID, EisaId ("USBC000"))  // _HID: Hardware ID
            Name (_CID, EisaId ("PNP0CA0"))  // _CID: Compatible ID
            Name (_UID, Zero)  // _UID: Unique ID
            Name (_DDN, "USB Type C")  // _DDN: DOS Device Name
            Name (_ADR, Zero)  // _ADR: Address
            Name (_DEP, Package (0x01)  // _DEP: Dependencies
            {
                \_SB.PCI0.SBRG.EC0
            })
            Name (M311, Buffer (0x14)
            {
                /* 0000 */  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  // ........
                /* 0008 */  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  // ........
                /* 0010 */  0x00, 0x00, 0x00, 0x00                           // ....
            })
            Name (CRS, ResourceTemplate ()
            {
                Memory32Fixed (ReadWrite,
                    0x00000000,         // Address Base
                    0x00001000,         // Address Length
                    _Y00)
            })
            Device (CR01)
            {
                Name (_ADR, Zero)  // _ADR: Address
                Method (_PLD, 0, NotSerialized)  // _PLD: Physical Location of Device
                {
                    CreateDWordField (M311, Zero, M312)
                    CreateDWordField (M311, 0x04, M313)
                    CreateDWordField (M311, 0x08, M314)
                    CreateDWordField (M311, 0x0C, M315)
                    CreateDWordField (M311, 0x10, M316)
                    Local0 = M310 /* External reference */
                    If (Local0)
                    {
                        Local0 += 0x4E
                        M312 = M013 ((Local0 + Zero), Zero, Zero, 0x20)
                        M313 = M013 ((Local0 + 0x04), Zero, Zero, 0x20)
                        M314 = M013 ((Local0 + 0x08), Zero, Zero, 0x20)
                        M315 = M013 ((Local0 + 0x0C), Zero, Zero, 0x20)
                        M316 = M013 ((Local0 + 0x10), Zero, Zero, 0x20)
                    }

                    Return (M311) /* \_SB_.UBTC.M311 */
                }
            }

            Method (_CRS, 0, Serialized)  // _CRS: Current Resource Settings
            {
                CreateDWordField (CRS, \_SB.UBTC._Y00._BAS, CBAS)  // _BAS: Base Address
                CBAS = M320 /* External reference */
                Return (CRS) /* \_SB_.UBTC.CRS_ */
            }

            Method (_STA, 0, NotSerialized)  // _STA: Status
            {
                If ((M049 (M128, 0x78) == One))
                {
                    Return (0x0F)
                }
                Else
                {
                    Return (Zero)
                }
            }

            OperationRegion (USBC, SystemMemory, M320, 0x30)
            Field (USBC, ByteAcc, Lock, Preserve)
            {
                VER1,   8, 
                VER2,   8, 
                RSV1,   8, 
                RSV2,   8, 
                CCI0,   8, 
                CCI1,   8, 
                CCI2,   8, 
                CCI3,   8, 
                CTL0,   8, 
                CTL1,   8, 
                CTL2,   8, 
                CTL3,   8, 
                CTL4,   8, 
                CTL5,   8, 
                CTL6,   8, 
                CTL7,   8, 
                MGI0,   8, 
                MGI1,   8, 
                MGI2,   8, 
                MGI3,   8, 
                MGI4,   8, 
                MGI5,   8, 
                MGI6,   8, 
                MGI7,   8, 
                MGI8,   8, 
                MGI9,   8, 
                MGIA,   8, 
                MGIB,   8, 
                MGIC,   8, 
                MGID,   8, 
                MGIE,   8, 
                MGIF,   8, 
                MGO0,   8, 
                MGO1,   8, 
                MGO2,   8, 
                MGO3,   8, 
                MGO4,   8, 
                MGO5,   8, 
                MGO6,   8, 
                MGO7,   8, 
                MGO8,   8, 
                MGO9,   8, 
                MGOA,   8, 
                MGOB,   8, 
                MGOC,   8, 
                MGOD,   8, 
                MGOE,   8, 
                MGOF,   8
            }

            Method (_DSM, 4, Serialized)  // _DSM: Device-Specific Method
            {
                If ((Arg0 == ToUUID ("6f8398c2-7ca4-11e4-ad36-631042b5008f") /* Unknown UUID */))
                {
                    If ((ToInteger (Arg2) == Zero))
                    {
                        Return (Buffer (One)
                        {
                             0x0F                                             // .
                        })
                    }
                    ElseIf ((ToInteger (Arg2) == One))
                    {
                        M000 (0x0DA8)
                        \_SB.PCI0.SBRG.EC0.MGO0 = MGO0 /* \_SB_.UBTC.MGO0 */
                        \_SB.PCI0.SBRG.EC0.MGO1 = MGO1 /* \_SB_.UBTC.MGO1 */
                        \_SB.PCI0.SBRG.EC0.MGO2 = MGO2 /* \_SB_.UBTC.MGO2 */
                        \_SB.PCI0.SBRG.EC0.MGO3 = MGO3 /* \_SB_.UBTC.MGO3 */
                        \_SB.PCI0.SBRG.EC0.MGO4 = MGO4 /* \_SB_.UBTC.MGO4 */
                        \_SB.PCI0.SBRG.EC0.MGO5 = MGO5 /* \_SB_.UBTC.MGO5 */
                        \_SB.PCI0.SBRG.EC0.MGO6 = MGO6 /* \_SB_.UBTC.MGO6 */
                        \_SB.PCI0.SBRG.EC0.MGO7 = MGO7 /* \_SB_.UBTC.MGO7 */
                        \_SB.PCI0.SBRG.EC0.MGO8 = MGO8 /* \_SB_.UBTC.MGO8 */
                        \_SB.PCI0.SBRG.EC0.MGO9 = MGO9 /* \_SB_.UBTC.MGO9 */
                        \_SB.PCI0.SBRG.EC0.MGOA = MGOA /* \_SB_.UBTC.MGOA */
                        \_SB.PCI0.SBRG.EC0.MGOB = MGOB /* \_SB_.UBTC.MGOB */
                        \_SB.PCI0.SBRG.EC0.MGOC = MGOC /* \_SB_.UBTC.MGOC */
                        \_SB.PCI0.SBRG.EC0.MGOD = MGOD /* \_SB_.UBTC.MGOD */
                        \_SB.PCI0.SBRG.EC0.MGOE = MGOE /* \_SB_.UBTC.MGOE */
                        \_SB.PCI0.SBRG.EC0.MGOF = MGOF /* \_SB_.UBTC.MGOF */
                        \_SB.PCI0.SBRG.EC0.CTL0 = CTL0 /* \_SB_.UBTC.CTL0 */
                        \_SB.PCI0.SBRG.EC0.CTL1 = CTL1 /* \_SB_.UBTC.CTL1 */
                        \_SB.PCI0.SBRG.EC0.CTL2 = CTL2 /* \_SB_.UBTC.CTL2 */
                        \_SB.PCI0.SBRG.EC0.CTL3 = CTL3 /* \_SB_.UBTC.CTL3 */
                        \_SB.PCI0.SBRG.EC0.CTL4 = CTL4 /* \_SB_.UBTC.CTL4 */
                        \_SB.PCI0.SBRG.EC0.CTL5 = CTL5 /* \_SB_.UBTC.CTL5 */
                        \_SB.PCI0.SBRG.EC0.CTL6 = CTL6 /* \_SB_.UBTC.CTL6 */
                        \_SB.PCI0.SBRG.EC0.CTL7 = CTL7 /* \_SB_.UBTC.CTL7 */
                        \_SB.PCI0.SBRG.EC0.ECMD (0x93)
                        M000 (0x0DA9)
                    }
                    ElseIf ((ToInteger (Arg2) == 0x02))
                    {
                        M000 (0x0DAA)
                        MGI0 = \_SB.PCI0.SBRG.EC0.MGI0 /* External reference */
                        MGI1 = \_SB.PCI0.SBRG.EC0.MGI1 /* External reference */
                        MGI2 = \_SB.PCI0.SBRG.EC0.MGI2 /* External reference */
                        MGI3 = \_SB.PCI0.SBRG.EC0.MGI3 /* External reference */
                        MGI4 = \_SB.PCI0.SBRG.EC0.MGI4 /* External reference */
                        MGI5 = \_SB.PCI0.SBRG.EC0.MGI5 /* External reference */
                        MGI6 = \_SB.PCI0.SBRG.EC0.MGI6 /* External reference */
                        MGI7 = \_SB.PCI0.SBRG.EC0.MGI7 /* External reference */
                        MGI8 = \_SB.PCI0.SBRG.EC0.MGI8 /* External reference */
                        MGI9 = \_SB.PCI0.SBRG.EC0.MGI9 /* External reference */
                        MGIA = \_SB.PCI0.SBRG.EC0.MGIA /* External reference */
                        MGIB = \_SB.PCI0.SBRG.EC0.MGIB /* External reference */
                        MGIC = \_SB.PCI0.SBRG.EC0.MGIC /* External reference */
                        MGID = \_SB.PCI0.SBRG.EC0.MGID /* External reference */
                        MGIE = \_SB.PCI0.SBRG.EC0.MGIE /* External reference */
                        MGIF = \_SB.PCI0.SBRG.EC0.MGIF /* External reference */
                        CCI0 = \_SB.PCI0.SBRG.EC0.CCI0 /* External reference */
                        CCI1 = \_SB.PCI0.SBRG.EC0.CCI1 /* External reference */
                        CCI2 = \_SB.PCI0.SBRG.EC0.CCI2 /* External reference */
                        CCI3 = \_SB.PCI0.SBRG.EC0.CCI3 /* External reference */
                        M000 (0x0DAB)
                    }
                    ElseIf ((ToInteger (Arg2) == 0x03))
                    {
                        Return (Zero)
                    }
                }

                Return (Zero)
            }
        }
    }
}

