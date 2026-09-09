# courtesy of Anuj Dahiya (https://github.com/anujdahiya24/FIDE/blob/main/Step%202%20-%20Reformat/Reformat%20Scripts/Reformat.Rmd)
# slight reformatting and removal of Kmisc dependency because it is deprecated

# Libraries
library(knitr)
library(tidyverse)
library(data.table)
library(foreach)
library(doParallel)
library(stringi)
library(lubridate)

# src/dst
path = "fide_historical_ratings"
destination = "fide_historical_ratings_formatted"


## Reformat the header
reformat <- function(file_csv, df) {
#Reformat October 2002
if(file_csv == "OCT02FRL.TXT"){df[1] <- df[1]%>%
                                           gsub("COUNTRY", "  Fed ", .)%>%
                                           gsub("GAMES", "Gms", .)%>%
                                           gsub("BIRTHDAY", " BIRTHDAY", .)}

#Reformat April 2003
else if(file_csv == "APR03FRL.TXT"){df[1] <- df[1]%>%
                                          gsub("   CODE  ","ID_NUMBER",.)%>%
                                          gsub("COUNTRY","  FED  ",.)%>%
                                          gsub(" APR03", "APR03 ", .)%>%
                                          gsub(" GAMES", "GMS   ", .)%>%
                                          gsub("  BIRTHDAY", "BIRTHDAY  ", .)%>%
                                          gsub(" FLAG", "FLAG ", .)}

#Reformat April, July, October 2004 & January, July 2005
else if(file_csv %in% c("APR04FRL.TXT","JUL04FRL.TXT","OCT04FRL.TXT", 
                        "JAN05FRL.TXT", "JUL05FRL.TXT")){
                                                df[1] <- df[1]%>%
                                                gsub("COUNTRY", "   FED ", . )%>%
                                                gsub("GAMES", "GAME ", .)%>%
                                                gsub(" BIRTHDAY", "BIRTHDAY", .)}

#Reformat January 2006 to July 2012
else if(file_csv == "JAN06FRL.TXT"){df <- df[-2]}
else if(file_csv %in% c("APR06FRL.TXT", "JUL06FRL.TXT", "OCT06FRL.TXT",
                      list.files(pattern = "[0][7-9][Ff][Rr][Ll].[Tt][Xx][Tt]"),
                      list.files(pattern = "[1][0-1][Ff][Rr][Ll].[Tt][Xx][Tt]"),
                      list.files(pattern = "[1][2][Ff][Rr][Ll].[Tt][Xx][Tt]")[1:5])){
                      df[1] <- df[1] %>% gsub("Titl", "Tit ", .)%>%
                                         gsub("Games", "Game ", .)%>%
                                         gsub("July", "Jul", .)}

#Insert underscore to make sure that proper columns are created in the functions afterwards
df[1] <- gsub("ID Number", "ID_NUMBER", df[1])%>%
         gsub("ID number", "ID_NUMBER", .)

return(df)
}

## indices at which to insert delimeters
indexes <- function(df){ 
column_vector<- df[1]
indexes <- rep(0, nchar(df[1]))
for(i in 1:nchar(column_vector)){
    index = grep("\\s[A-z]", substr(column_vector, i, i+1))
    if (identical(index, integer(0)) == TRUE){indexes[i] = 0}
    else {indexes[i] = 1}
                                }
return(which(indexes == 1))
}


## Insert delimiters quickly
utf_func <- function(df, indexed){
  string <- utf8ToInt(df)
  string[indexed] <- utf8ToInt("*")
  return(intToUtf8(string))
}


## rename file to consistent format
filenamer <- function(Year_num) {
  Year_num%>%
    substr(., nchar(.)-11, nchar(.)-7)%>%
    toupper()%>%
    paste(destination, ., ".csv", sep = "")
}


## Write files
fwrite_wrapper <- function(filename, df){
if (file.exists(filename)) {unlink(filename)}
fwrite(list(df), file = filename, quote = FALSE)
}


## All files write
All_files_fwrite <- function(year_vector){
text_insert_first = c("jul03frl.txt","OCT03FRL.TXT", "JAN04FRL.TXT", 
                      "APR05FRL.TXT", "jan03frl.txt")
columns = "ID_NUMBER NAME                            TITLE FED  RATING GM  Bday      Flag "

if(year_vector %in% text_insert_first){
df = readLines(year_vector)
  if(nchar(df[1]) != 0) {
    cat("", df, file = year_vector, sep = "\n")
    df <- readLines(year_vector)
    df[1] <- columns} else{df[1] <- columns}
} else {df = readLines(year_vector)}
  
df <- reformat(year_vector, df)
indexed = indexes(df)
df = sapply(df , utf_func, indexed = indexed, USE.NAMES = FALSE)
filename <- filenamer(year_vector)
fwrite_wrapper(df, file = filename)
}


## Multi Processing
multi_processing <- function(Year_num){
                    functions = ls(globalenv())
                    cl <- makeCluster(detectCores()) 
                    clusterExport(cl, functions)
                    registerDoParallel(cl)
                    foreach(i = Year_num,
                            .export = functions,
                            .packages = c("dplyr", 
                                          "data.table")) %dopar% {All_files_fwrite(i)}
                    stopCluster(cl)
}


# A final touch and output
Year_num <- list.files(path = path, pattern = "[Ff][Rr][Ll].[Tt][Xx][Tt]")

setwd(path)

# took about 3 min
system.time(multi_processing(Year_num))

##Run this if parallel processing doesn't work
# system.time(invisible(mapply(All_files_fwrite, Year_num)))

head(list.files(path = destination, pattern = "*.csv"))
