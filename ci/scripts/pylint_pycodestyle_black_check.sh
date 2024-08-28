#!/bin/bash +x

# Usage: pylint_pycodestyle_black_check.sh <workspace_path>

WORKSPACE="$1"

READ_FLAG=false

echo -e "\n -------- Checking the Pylint and Pycodestyle rules and Black formatting on the changes -------- \n"

# avoid fatal error: detected dubious ownership in repository
git config --global --add safe.directory "${WORKSPACE}"

# shellcheck disable=SC2006
files=`git log -1 --diff-filter=ACMTR --name-only --pretty=format: FETCH_HEAD | grep -E '.py'`

for file in $files; do
  if [ "${file: -3}" == ".py" ]; then
    READ_FLAG=true
    echo "Checking file : ${file}"
    python -m pylint --load-plugins=pylint.extensions.docparams "${WORKSPACE}"/"${file}" >> pylint.log
    python -m pycodestyle --show-source --ignore=E501,W605,E731,E203,W503 "${WORKSPACE}"/"${file}" >> pycodestyle.log
    python -m black "${WORKSPACE}"/"${file}" 2>> black.log
  fi
done

if [ "$READ_FLAG" = true ]; then
  # shellcheck disable=SC2006
  read_pylint_log=`cat "${WORKSPACE}"/pylint.log`
  # shellcheck disable=SC2006
  read_black_log=`cat "${WORKSPACE}"/black.log`

  if [[ ! $read_pylint_log = *"*************"* ]] && [[ ! -s  ${WORKSPACE}/pycodestyle.log ]] && [[ ! $read_black_log = *"reformatted"* ]]; then
      cat "${WORKSPACE}"/pylint.log
      echo -e '\nSUCCESS : Pylint check Succeeded'
      echo 'SUCCESS : Pycodestyle check Succeeded'
      echo 'SUCCESS : Black check Succeeded'
      exit 0
  else
      if [[ $read_pylint_log = *"*************"* ]]; then
          echo -e "\nPylint version: $(pylint --version | grep pylint)"
          echo -e "\nThe following are the Pylint issues : "
          cat "${WORKSPACE}"/pylint.log
          echo -e "\nERROR : Build Failed because of pylint rules!"
      else
          echo -e "\nPylint check: PASSED"
      fi

      if [[ -s  ${WORKSPACE}/pycodestyle.log ]]; then
          echo -e "\nThe following are the Pycodestyle issues : "
          cat "${WORKSPACE}"/pycodestyle.log
          echo -e "\nERROR : Build Failed because of pycodestyle rules!"
      else
          echo -e "\nPycodestyle check: PASSED"
      fi

      if [[ $read_black_log = *"reformatted"* ]]; then
          echo -e "\nBlack version: $(black --version | grep black)"
          echo -e "\nThe following files were reformatted by Black: "
          cat "${WORKSPACE}"/black.log
          echo -e "\nERROR : Build Failed because of poorly formatted files!"
          echo -e "\nTo fix the problem, please run Black before committing any changes!"
      else
          echo -e "\nBlack check: PASSED"
      fi
      echo -e "\nPylint, Pycodestyle and Black checks finished"
      exit 1
  fi
else
    echo -e "\nNo python files found. Skipping the Pylint, Pycodestyle and Black checks."
    exit 0
fi