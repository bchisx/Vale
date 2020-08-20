import unittest
import subprocess
import os.path
import os
import sys
import shutil
import glob

from typing import Dict, Any, List, Callable


def procrun(args: List[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kwargs)


PATH_TO_SAMPLES = "../Valestrom/Samples/test/main/resources/"

class ValeTest(unittest.TestCase):
    GENPATH: str = os.environ.get('GENPATH', "cmake-build-debug")

    def valestrom(self, vale_filepaths: List[str],
                  vir_file: str) -> subprocess.CompletedProcess:
        driver = "test/Driver.jar"
        driver_class = "net.verdagon.vale.driver.Driver"
        return procrun(
            [
                "java",
                "-cp",
                driver,
                driver_class,
                "build",
                "-o",
                vir_file
            ] +
            vale_filepaths
        )

    def valec(self, vir_file: str,
              o_files_dir: str,
              region_override: str) -> subprocess.CompletedProcess:
        assert self.GENPATH
        return procrun(
            [f"{self.GENPATH}/valec", "--verify", "--llvmir", "--census", "--region-override", region_override, "--output-dir",
             o_files_dir, vir_file])

    def clang(self, o_files: List[str],
              exe_file: str) -> subprocess.CompletedProcess:
        return procrun(["clang", "-o", exe_file] + o_files)

    def exec(self, exe_file: str) -> subprocess.CompletedProcess:
        return procrun([f"./{exe_file}"])

    @classmethod
    def setUpClass(cls) -> None:
        print(
            f"Using valec from {cls.GENPATH}. " +
            "Set GENPATH env var if this is incorrect",
            file=sys.stderr
        )

    def setUp(self) -> None:
        self.GENPATH: str = type(self).GENPATH

    def compile_and_execute(
            self, vale_filepaths: List[str], region_override: str) -> subprocess.CompletedProcess:
        last_vale_filepath = vale_filepaths[len(vale_filepaths) - 1]
        file_name_without_extension = os.path.splitext(os.path.basename(last_vale_filepath))[0]
        build_dir = f"test/test_build/{file_name_without_extension}_build"

        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        os.makedirs(build_dir)

        vir_file = f"{build_dir}/{file_name_without_extension}.vir"
        proc = self.valestrom(vale_filepaths, vir_file)
        # print(proc.stdout)
        # print(proc.stderr)
        self.assertEqual(proc.returncode, 0,
                         f"valestrom couldn't compile {file_name_without_extension}:\n" +
                         proc.stdout + "\n" + proc.stderr)

        proc = self.valec(vir_file, build_dir, region_override)
        self.assertEqual(proc.returncode, 0,
                         f"valec couldn't compile {vir_file}:\n" +
                         proc.stdout + "\n" + proc.stderr)

        exe_file = f"{build_dir}/{file_name_without_extension}"
        o_files = glob.glob(f"{build_dir}/*.o") + ["src/valestd/assert.c", "src/valestd/stdio.c", "src/valestd/str.c", "src/valestd/census.c", "src/valestd/weaks.c"]
        proc = self.clang(o_files, exe_file)
        self.assertEqual(proc.returncode, 0,
                         f"clang couldn't compile {o_files}:\n" +
                         proc.stdout + "\n" + proc.stderr)

        proc = self.exec(exe_file)
        return proc

    def compile_and_execute_and_expect_return_code(self, vale_files: List[str],
                                                   expected_return_code) -> None:
        proc = self.compile_and_execute(vale_files, "assist")
        # print(proc.stdout)
        # print(proc.stderr)
        self.assertEqual(proc.returncode, expected_return_code,
                         f"Unexpected result: {proc.returncode}\n" + proc.stdout + proc.stderr)

        proc = self.compile_and_execute(vale_files, "unsafe-fast")
        # print(proc.stdout)
        # print(proc.stderr)
        self.assertEqual(proc.returncode, expected_return_code,
                         f"Unexpected result: {proc.returncode}\n" + proc.stdout + proc.stderr)

        proc = self.compile_and_execute(vale_files, "resilient")
        # print(proc.stdout)
        # print(proc.stderr)
        self.assertEqual(proc.returncode, expected_return_code,
                         f"Unexpected result: {proc.returncode}\n" + proc.stdout + proc.stderr)

    def test_addret(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "addret.vale"],
            7)

    def test_immstruct(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "structs/immstruct.vale"],
            5)

    def test_memberrefcount(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "structs/memberrefcount.vale"],
            5)

    def test_bigimmstruct(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "structs/bigimmstruct.vale"],
            42)

    def test_mutstruct(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "structs/mutstruct.vale"],
            8)

    def test_lambda(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "lambdas/lambda.vale"],
            42)

    def test_if(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "if/if.vale"],
            42)

    def test_mutlocal(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "mutlocal.vale"],
            42)

    def test_while(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "while/while.vale"],
            42)

    def test_constraintRef(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "constraintRef.vale"],
            8)

    def test_knownsizeimmarray(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "arrays/knownsizeimmarray.vale"],
            42)

    def test_imminterface(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "virtuals/imminterface.vale"],
            42)

    def test_mutinterface(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "virtuals/mutinterface.vale"],
            42)

    def test_mutstructstore(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "structs/mutstructstore.vale"],
            42)

    def test_immusa(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "arrays/immusa.vale"],
            3)

    def test_immusalen(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "arrays/immusalen.vale"],
            5)

    def test_mutusa(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "arrays/mutusa.vale"],
            3)

    def test_mutusalen(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "arrays/mutusalen.vale"],
            5)

    def test_stradd(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "strings/stradd.vale"],
            42)

    def test_lambdamut(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "lambdas/lambdamut.vale"],
            42)

    def test_strprint(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "strings/strprint.vale"],
            42)

    def test_inttostr(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "strings/inttostr.vale"],
            42)

    def test_nestedif(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "if/nestedif.vale"],
            42)

    def test_unstackifyret(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "unstackifyret.vale"],
            42)

    def test_swapmutusadestroy(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "arrays/swapmutusadestroy.vale"],
            42)

    def test_unreachablemoot(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "unreachablemoot.vale"],
            42)

    def test_panic(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "panic.vale"],
            42)

    def test_nestedblocks(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "nestedblocks.vale"],
            42)

    def test_dropThenLockStruct(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "genericvirtuals/opt.vale",
             PATH_TO_SAMPLES + "weaks/dropThenLockStruct.vale"],
            42)

    def test_lockWhileLiveStruct(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "genericvirtuals/opt.vale",
             PATH_TO_SAMPLES + "weaks/lockWhileLiveStruct.vale"],
            7)

    def test_weakFromLocalCRefStruct(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "genericvirtuals/opt.vale",
             PATH_TO_SAMPLES + "weaks/weakFromLocalCRefStruct.vale"],
            7)

    def test_weakFromCRefStruct(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "genericvirtuals/opt.vale",
             PATH_TO_SAMPLES + "weaks/weakFromCRefStruct.vale"],
            7)

    def test_dropThenLockInterface(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "genericvirtuals/opt.vale",
             PATH_TO_SAMPLES + "weaks/dropThenLockInterface.vale"],
            42)

    def test_lockWhileLiveInterface(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "genericvirtuals/opt.vale",
             PATH_TO_SAMPLES + "weaks/lockWhileLiveInterface.vale"],
            7)

    def test_weakFromLocalCRefInterface(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "genericvirtuals/opt.vale",
             PATH_TO_SAMPLES + "weaks/weakFromLocalCRefInterface.vale"],
            7)

    def test_weakFromCRefInterface(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "genericvirtuals/opt.vale",
             PATH_TO_SAMPLES + "weaks/weakFromCRefInterface.vale"],
            7)


    def test_callWeakSelfMethodWhileLive(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "genericvirtuals/opt.vale",
             PATH_TO_SAMPLES + "weaks/callWeakSelfMethodWhileLive.vale"],
            42)

    def test_callWeakSelfMethodAfterDrop(self) -> None:
        self.compile_and_execute_and_expect_return_code(
            [PATH_TO_SAMPLES + "genericvirtuals/opt.vale",
             PATH_TO_SAMPLES + "weaks/callWeakSelfMethodAfterDrop.vale"],
            0)


if __name__ == '__main__':
    unittest.main()
