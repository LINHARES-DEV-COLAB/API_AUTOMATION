class TrataEmpresa():
    usuario = ""
    senha = ""
    emp = ""
    def trataEmp(EMP: str) -> str:
        if EMP == "TA":
            TrataEmpresa.login = "42549981391"
            TrataEmpresa.senha = "cariri1627"
            TrataEmpresa.emp = "NHAMUNS MOTOS LTDA - 02317298000"
            return TrataEmpresa
        else:
            TrataEmpresa.login = "02010339339"
            TrataEmpresa.senha = "wvZpuZ0o"
            match EMP:
                case "JU":
                    TrataEmpresa.emp = "ARES JUAZEIRO - 07256867000151"
                    return TrataEmpresa
                
                case "AC":
                    TrataEmpresa.emp = "ARES ACM"
                    return TrataEmpresa
                
                case "AR":
                    TrataEmpresa.emp = "ARES ARACATI"
                    return TrataEmpresa
                
                case "CS":
                    TrataEmpresa.emp = "ARES C SA"
                    return TrataEmpresa
                
                case "BJ":
                    TrataEmpresa.emp = "ARES BRE"
                    return TrataEmpresa
                
                case "CA":
                    TrataEmpresa.emp = "ARES MOTOS CALC"
                    return TrataEmpresa
                
                case "CDA":
                    TrataEmpresa.emp = "ARES MOTOS CD"
                    return TrataEmpresa
                
                case "CR":
                    TrataEmpresa.emp = "ARES MOTOS CRAT"
                    return TrataEmpresa
                
                case "IC":
                    TrataEmpresa.emp = "ARES MOTOS IC"
                    return TrataEmpresa
                
                case "IG":
                    TrataEmpresa.emp = "ARES MOTOS IGU"
                    return TrataEmpresa
                
                case "IP":
                    TrataEmpresa.emp = "ARES MOTOS IP"
                    return TrataEmpresa
                
                case "IT":
                    TrataEmpresa.emp = "ARES MOTOS ITAPI"
                    return TrataEmpresa
                
                case "PA":
                    TrataEmpresa.emp = "ARES MOTOS P"
                    return TrataEmpresa
                
                case "LI":
                    TrataEmpresa.emp = "ARES MOTOS LIT"
                    return TrataEmpresa

                case "PG":
                    TrataEmpresa.emp = "ARES MOTOS ITAPA"
                    return TrataEmpresa

                case "TI":
                    TrataEmpresa.emp = "ARES MOTOS TIAN"
                    return TrataEmpresa
                
                case "VA":
                    TrataEmpresa.emp = "ARES MOTOS VAL"
                    return TrataEmpresa
                
                case _:
                    return ""

        