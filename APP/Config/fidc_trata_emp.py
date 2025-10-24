def trataEmp(EMP: str) -> str:
    match EMP:
        case "JU":
            return "ARES JUAZEIR"
        case "AC":
            return "ARES ACM"
        case "AR":
            return "ARES ARACATI"
        case "CS":
            return "ARES C SA"
        case "BJ":
            return "ARES BRE"
        case "CA":
            return "ARES MOTOS CALC"
        case "CDA":
            return "ARES MOTOS CD"
        case "CR":
            return "ARES CRAT"
        case "IC":
            return "ARES IC"
        case "IG":
            return "ARES IGU"
        case "IP":
            return "ARES IP"
        case "IT":
            return "ARES ITAPI"
        case "LA":
            return ""
        case "PA":
            return "ARES P"
        case "LI":
            return "ARES MOTOS LIT"
        case "NI":
            return ""
        case "PG":
            return "ARESARES ITAPA"
        case "SV":
            return ""
        case "TA":
            return "INHA"
        case "TI":
            return "ARES TIAN"
        case "VA":
            return "ARES MOTOS VAL"
        case _:
            return ""

    