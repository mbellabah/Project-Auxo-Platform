import pytest 
import pathlib
import shutil
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from auxo_mount_olympus.gen import gen


CWD = pathlib.Path.cwd()   
SERVICES_PATH = CWD.joinpath("../../auxo_olympus/lib/services")


# setup 
service_name = "Dummy Test"
author = "Test"
description = "Just a test"
last_modified = "NA"
data = {"name": service_name, "author": author, "description": description, "last_modified": last_modified}


@pytest.fixture(scope="session")
def services_folder(tmpdir_factory): 
    # test fixture creates a temporary directory (it deletes it once the tests are done)
    my_tempdir = tmpdir_factory.mktemp("services")
    gen.generate(my_tempdir, service_name, author, description, last_modified)
    """
    EXPECTED FOLDER: 
    ....services/
        serviceExeDummyTest/
            __init__.py
            serviceExeDummyTest.py
                -> Populated with the generator template stuff
            serviceExeDummyTest.txt
                -> Name: Dummy Test
                   Author: Test
                   Last Modified: NA
                   Description: Just a test 
    """
    yield pathlib.Path(my_tempdir.realpath())
    shutil.rmtree(str(my_tempdir))   


class TestGen: 
    def test_folder_exists(self, services_folder):
        assert (services_folder / "serviceExeDummyTest").is_dir(), "serviceExeDummyTest folder does not exist"
    
    def test_py_file_exists(self, services_folder): 
        assert (services_folder / "serviceExeDummyTest" / "serviceExeDummyTest.py").is_file() and (services_folder / "serviceExeDummyTest" / "__init__.py").is_file(), "Incorrect __init__.py or serviceExeDummyTest.py"

    def test_txt_file_exists(self, services_folder): 
        assert (services_folder / "serviceExeDummyTest" / "serviceExeDummyTest.txt").is_file(), "serviceExeDummyTest.txt does not exist"
    
    def test_txt_file(self, services_folder): 
        """ Ensure that the .txt file contains the correct things """ 
        f = services_folder / "serviceExeDummyTest" / "serviceExeDummyTest.txt"
        services = {}
        read_file = open(f, "r")

        name = read_file.readline().split(":")[1].strip()
        author = read_file.readline().split(":")[1].strip()
        last_modified = read_file.readline().split(":")[1].strip()
        description = read_file.read().split(":")[1].strip()

        services = {"name": name, "author": author, "description": description, "last_modified": last_modified}
        read_file.close() 
        
        assert data == services, "serviceExeDummyTest.txt contents are incorrect"

    @pytest.mark.xfail(raises=TemplateNotFound, reason="tempdir does not have the template, don't even run", run=False)
    def test_py_file(self, services_folder):
        # Simply checks to see if the .py file is populated 
        f = services_folder / "serviceExeDummyTest" / "serviceExeDummyTest.py"
        assert f.stat().st_size != 0, "serviceExeDummyTest.py is not populated"
