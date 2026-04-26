4/6/26, 2:27 PM 

config-api reference 

All Topics 

## **config-api reference** 

Travel configuration data sourced predominantly from the Outtask database. 

## **Contact** 

#ask-travel-admin-config on Slack 

https://concur-blue.slack.com/archives/CNS5TNF9U 

## **API ENDPOINTS** 

```
# Integration:
https://integration.api.concursolutions.com/config-api/graphql
# US:
https://us.api.concursolutions.com/config-api/graphql
# EU1:
https://eu1.api.concursolutions.com/config-api/graphql
# EU2:
https://eu2.api.concursolutions.com/config-api/graphql
# USPSCC:
https://usg.api.concursolutions.com/config-api/graphql
```

## **HEADERS** 

```
# The CN for your service must be registered with our service.
Authorization: Bearer <YOUR_TOKEN_HERE>
# Please provide a correlation id for debugging
concur-correlationid: 26c25791-5509-4c6e-81c5-8ecbb87cc312
# Please only use application/json along with a POST request moving forward. Do not use appl
Content-Type: application/json
# The above is the best practice value to send according to GraphQL specification.
Accept: application/graphql-response+json
```

## Queries 

## **authZ** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

1/246 

4/6/26, 2:27 PM 

config-api reference 

Authorization check used by admin UI 

Response 

Returns an `AuthZ` 

## **QUERY** 

```
query AuthZ {
authZ {
tripLinkAdmin
companySelect
  }
}
```

## **RESPONSE** 

```
{"data": {"authZ": {"tripLinkAdmin": false, "companySelect": false}}}
```

Queries 

## **companiesByAgency** 

JWT Roles: travelsysadmin, sysadmin, travelagentadmin, techsupportadmin, or techsupportadmindevpm 

Response 

Returns `[Company]` 

Arguments 

Name Description 

`nameFilter` - `String` 

## **QUERY** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

2/246 

4/6/26, 2:27 PM 

config-api reference 

```
query CompaniesByAgency($nameFilter: String) {
  companiesByAgency(nameFilter: $nameFilter){
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
migrationReadyUtc
migratedElsewhere
    }
directBillContractReferenceId
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
customText {
fieldName
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

3/246 

4/6/26, 2:27 PM 

config-api reference 

```
languageCode
value
useDefault
    }
domains {
name
companyId
isDefault
    }
publishedFiles {
fileId
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
locations {
id
uuid
companyId
name
address
city
state
zipCode
countryCode
latitude
longitude
allowDelivery
vendors {
...LocationVendorFragment
      }
    }
modules {
companyId
moduleCode
isActive
moduleProperties {
...ModulePropertyFragment
      }
    }
orgUnits {
orgUnitId
uuid
orgUnitName
    }
ruleClasses {
id
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

4/246 

4/6/26, 2:27 PM 

config-api reference 

```
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
travelConfigs {
id
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
...PublishedFileFragment
      }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
...AgencyConfigFragment
      }
company {
...CompanyFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

5/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
configurationItems {
...ConfigurationItemFragment
      }
configurationItemsHistory {
...ConfigurationItemFragment
      }
consortiumHotels {
...ConsortiumHotelFragment
      }
contractHotels {
...ContractHotelFragment
      }
customFields {
...CustomFieldFragment
      }
eReceipt {
...EReceiptFragment
      }
emailOptions {
...EmailOptionsFragment
      }
formOfPayment {
...FormOfPaymentFragment
      }
hotelSearch {
...HotelSearchFragment
      }
pnrFinishing {
...PnrFinishingFragment
      }
profileOptions {
...ProfileOptionsFragment
      }
wizardOptions {
...WizardOptionsFragment
      }
domains {
...TravelConfigDomainFragment
      }
travelConfigItems {
...TravelConfigItemFragment
      }
tsaSecureFlight {
...TsaSecureFlightFragment
      }
profileSyncOptions {
...ProfileSyncOptionsFragment
      }
vendorDiscounts {
...VendorDiscountFragment
      }
vendorExclusions {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

6/246 

4/6/26, 2:27 PM 

config-api reference 

```
...VendorExclusionFragment
      }
violationReasons {
...ViolationReasonFragment
      }
gdsPnr {
...GdsPnrFragment
      }
bookingSourceOptions {
...BookingSourceOptionFragment
      }
hotelShop {
...HotelShopFragment
      }
customText {
...CustomTextFragment
      }
carSearch {
...CarSearchFragment
      }
sharedCustomFields {
...SharedCustomFieldFragment
      }
tripOptions {
...TripOptionsFragment
      }
currencyCode
policyOptions {
...PolicyOptionsFragment
      }
airSearch {
...AirSearchFragment
      }
sabreProfile {
...SabreProfileFragment
      }
airportHubs {
...AirportHubFragment
      }
t2OptIn {
...T2OptInFragment
      }
configOptions {
...ConfigurationOptionsFragment
      }
railConnector {
...RailConnectorFragment
      }
hasFutureHotelSeasonalRates
ruleClass {
...RuleClassFragment
      }
ruleClasses {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

7/246 

4/6/26, 2:27 PM 

config-api reference 

```
...RuleClassFragment
      }
egenciaIntegration
contractExternalReferenceId
    }
companyGroups {
groupId
groupName
uuid
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
partnerServiceVendors {
baseUrl
domain
login
password
vendorId
vendorCode
vendorName
vendorLogo
microserviceUrl
apiVersion
billingReferenceId
shortVendorName
systemRequestorId
systemRequestorIdType
vendorStatus
    }
  }
}
```

## **VARIABLES** 

```
{"nameFilter": "xyz789"}
```

## **RESPONSE** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

8/246 

4/6/26, 2:27 PM 

config-api reference 

```
{
"data": {
"companiesByAgency": [
      {
"id": "abc123",
"companyId": 123,
"companyName": "abc123",
"internetDomain": "xyz789",
"companyDomain": "abc123",
"countryCode": "xyz789",
"billingCurrencyCode": "abc123",
"uuid": "xyz789",
"activeSwitch": 123,
"isBillable": true,
"travelOfferingCode": "xyz789",
"isUatCompany": true,
"migration": Migration,
"directBillContractReferenceId": "abc123",
"customFields": [CustomField],
"customText": [CustomText],
"domains": [Domain],
"publishedFiles": [PublishedFile],
"locations": [Location],
"modules": [Module],
"orgUnits": [OrgUnit],
"ruleClasses": [RuleClass],
"travelConfigs": [TravelConfig],
"companyGroups": [CompanyGroup],
"t2OptIn": T2OptIn,
"partnerServiceVendors": [PartnerServiceVendor]
      }
    ]
  }
}
```

Queries 

## **companiesByAgencyUuid** 

JWT Roles: travelsysadmin, sysadmin, travelagentadmin, techsupportadmin, or techsupportadmindevpm 

## Response 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

9/246 

4/6/26, 2:27 PM 

config-api reference 

Returns `[Company]` 

Arguments 

Name Description 

`uuid` - `String!` 

`nameFilter` - `String` 

## **QUERY** 

```
query CompaniesByAgencyUuid(
$uuid: String!,
$nameFilter: String
){
companiesByAgencyUuid(
    uuid: $uuid,
    nameFilter: $nameFilter
  ){
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
migrationReadyUtc
migratedElsewhere
    }
directBillContractReferenceId
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

10/246 

4/6/26, 2:27 PM 

config-api reference 

```
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
customText {
fieldName
languageCode
value
useDefault
    }
domains {
name
companyId
isDefault
    }
publishedFiles {
fileId
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
locations {
id
uuid
companyId
name
address
city
state
zipCode
countryCode
latitude
longitude
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

11/246 

4/6/26, 2:27 PM 

config-api reference 

```
allowDelivery
vendors {
...LocationVendorFragment
      }
    }
modules {
companyId
moduleCode
isActive
moduleProperties {
...ModulePropertyFragment
      }
    }
orgUnits {
orgUnitId
uuid
orgUnitName
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
travelConfigs {
id
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
...PublishedFileFragment
      }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

12/246 

4/6/26, 2:27 PM 

config-api reference 

```
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
...AgencyConfigFragment
      }
company {
...CompanyFragment
      }
configurationItems {
...ConfigurationItemFragment
      }
configurationItemsHistory {
...ConfigurationItemFragment
      }
consortiumHotels {
...ConsortiumHotelFragment
      }
contractHotels {
...ContractHotelFragment
      }
customFields {
...CustomFieldFragment
      }
eReceipt {
...EReceiptFragment
      }
emailOptions {
...EmailOptionsFragment
      }
formOfPayment {
...FormOfPaymentFragment
      }
hotelSearch {
...HotelSearchFragment
      }
pnrFinishing {
...PnrFinishingFragment
      }
profileOptions {
...ProfileOptionsFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

13/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
wizardOptions {
...WizardOptionsFragment
      }
domains {
...TravelConfigDomainFragment
      }
travelConfigItems {
...TravelConfigItemFragment
      }
tsaSecureFlight {
...TsaSecureFlightFragment
      }
profileSyncOptions {
...ProfileSyncOptionsFragment
      }
vendorDiscounts {
...VendorDiscountFragment
      }
vendorExclusions {
...VendorExclusionFragment
      }
violationReasons {
...ViolationReasonFragment
      }
gdsPnr {
...GdsPnrFragment
      }
bookingSourceOptions {
...BookingSourceOptionFragment
      }
hotelShop {
...HotelShopFragment
      }
customText {
...CustomTextFragment
      }
carSearch {
...CarSearchFragment
      }
sharedCustomFields {
...SharedCustomFieldFragment
      }
tripOptions {
...TripOptionsFragment
      }
currencyCode
policyOptions {
...PolicyOptionsFragment
      }
airSearch {
...AirSearchFragment
      }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

14/246 

4/6/26, 2:27 PM 

config-api reference 

```
sabreProfile {
...SabreProfileFragment
      }
airportHubs {
...AirportHubFragment
      }
t2OptIn {
...T2OptInFragment
      }
configOptions {
...ConfigurationOptionsFragment
      }
railConnector {
...RailConnectorFragment
      }
hasFutureHotelSeasonalRates
ruleClass {
...RuleClassFragment
      }
ruleClasses {
...RuleClassFragment
      }
egenciaIntegration
contractExternalReferenceId
    }
companyGroups {
groupId
groupName
uuid
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
partnerServiceVendors {
baseUrl
domain
login
password
vendorId
vendorCode
vendorName
vendorLogo
microserviceUrl
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

15/246 

4/6/26, 2:27 PM 

config-api reference 

```
apiVersion
billingReferenceId
shortVendorName
systemRequestorId
systemRequestorIdType
vendorStatus
    }
  }
}
```

## **VARIABLES** 

```
{
"uuid": "abc123",
"nameFilter": "xyz789"
}
```

## **RESPONSE** 

```
{
"data": {
"companiesByAgencyUuid": [
      {
"id": "abc123",
"companyId": 123,
"companyName": "xyz789",
"internetDomain": "abc123",
"companyDomain": "xyz789",
"countryCode": "xyz789",
"billingCurrencyCode": "abc123",
"uuid": "xyz789",
"activeSwitch": 123,
"isBillable": false,
"travelOfferingCode": "xyz789",
"isUatCompany": true,
"migration": Migration,
"directBillContractReferenceId": "xyz789",
"customFields": [CustomField],
"customText": [CustomText],
"domains": [Domain],
"publishedFiles": [PublishedFile],
"locations": [Location],
"modules": [Module],
"orgUnits": [OrgUnit],
"ruleClasses": [RuleClass],
"travelConfigs": [TravelConfig],
"companyGroups": [CompanyGroup],
"t2OptIn": T2OptIn,
"partnerServiceVendors": [PartnerServiceVendor]
      }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

16/246 

4/6/26, 2:27 PM 

config-api reference 

```
}
```

Queries 

## **companiesByModulePropertyNameA…** 

Response 

Returns `[Company]` 

Arguments 

Name Description 

`module` - `String!` 

`propertyName` - `String!` 

`propertyValue` - `String!` 

## **QUERY** 

```
query CompaniesByModulePropertyNameAndValue(
$module: String!,
$propertyName: String!,
$propertyValue: String!
){
companiesByModulePropertyNameAndValue(
    module: $module,
    propertyName: $propertyName,
    propertyValue: $propertyValue
  ){
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

17/246 

4/6/26, 2:27 PM 

config-api reference 

```
isBillable
travelOfferingCode
isUatCompany
migration {
migrationReadyUtc
migratedElsewhere
    }
directBillContractReferenceId
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
customText {
fieldName
languageCode
value
useDefault
    }
domains {
name
companyId
isDefault
    }
publishedFiles {
fileId
companyId
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

18/246 

4/6/26, 2:27 PM 

config-api reference 

```
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
locations {
id
uuid
companyId
name
address
city
state
zipCode
countryCode
latitude
longitude
allowDelivery
vendors {
...LocationVendorFragment
      }
    }
modules {
companyId
moduleCode
isActive
moduleProperties {
...ModulePropertyFragment
      }
    }
orgUnits {
orgUnitId
uuid
orgUnitName
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

19/246 

4/6/26, 2:27 PM 

config-api reference 

```
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
travelConfigs {
id
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
...PublishedFileFragment
      }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
...AgencyConfigFragment
      }
company {
...CompanyFragment
      }
configurationItems {
...ConfigurationItemFragment
      }
configurationItemsHistory {
...ConfigurationItemFragment
      }
consortiumHotels {
...ConsortiumHotelFragment
      }
contractHotels {
...ContractHotelFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

20/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
customFields {
...CustomFieldFragment
      }
eReceipt {
...EReceiptFragment
      }
emailOptions {
...EmailOptionsFragment
      }
formOfPayment {
...FormOfPaymentFragment
      }
hotelSearch {
...HotelSearchFragment
      }
pnrFinishing {
...PnrFinishingFragment
      }
profileOptions {
...ProfileOptionsFragment
      }
wizardOptions {
...WizardOptionsFragment
      }
domains {
...TravelConfigDomainFragment
      }
travelConfigItems {
...TravelConfigItemFragment
      }
tsaSecureFlight {
...TsaSecureFlightFragment
      }
profileSyncOptions {
...ProfileSyncOptionsFragment
      }
vendorDiscounts {
...VendorDiscountFragment
      }
vendorExclusions {
...VendorExclusionFragment
      }
violationReasons {
...ViolationReasonFragment
      }
gdsPnr {
...GdsPnrFragment
      }
bookingSourceOptions {
...BookingSourceOptionFragment
      }
hotelShop {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

21/246 

4/6/26, 2:27 PM 

config-api reference 

```
...HotelShopFragment
      }
customText {
...CustomTextFragment
      }
carSearch {
...CarSearchFragment
      }
sharedCustomFields {
...SharedCustomFieldFragment
      }
tripOptions {
...TripOptionsFragment
      }
currencyCode
policyOptions {
...PolicyOptionsFragment
      }
airSearch {
...AirSearchFragment
      }
sabreProfile {
...SabreProfileFragment
      }
airportHubs {
...AirportHubFragment
      }
t2OptIn {
...T2OptInFragment
      }
configOptions {
...ConfigurationOptionsFragment
      }
railConnector {
...RailConnectorFragment
      }
hasFutureHotelSeasonalRates
ruleClass {
...RuleClassFragment
      }
ruleClasses {
...RuleClassFragment
      }
egenciaIntegration
contractExternalReferenceId
    }
companyGroups {
groupId
groupName
uuid
    }
t2OptIn {
airOptIn
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

22/246 

4/6/26, 2:27 PM 

config-api reference 

```
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
partnerServiceVendors {
baseUrl
domain
login
password
vendorId
vendorCode
vendorName
vendorLogo
microserviceUrl
apiVersion
billingReferenceId
shortVendorName
systemRequestorId
systemRequestorIdType
vendorStatus
    }
  }
}
```

## **VARIABLES** 

```
{
"module": "abc123",
"propertyName": "abc123",
"propertyValue": "xyz789"
}
```

## **RESPONSE** 

```
{
"data": {
"companiesByModulePropertyNameAndValue": [
      {
"id": "abc123",
"companyId": 987,
"companyName": "abc123",
"internetDomain": "xyz789",
"companyDomain": "xyz789",
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

23/246 

4/6/26, 2:27 PM 

config-api reference 

```
"countryCode": "abc123",
"billingCurrencyCode": "xyz789",
"uuid": "xyz789",
"activeSwitch": 987,
"isBillable": true,
"travelOfferingCode": "abc123",
"isUatCompany": false,
"migration": Migration,
"directBillContractReferenceId": "xyz789",
"customFields": [CustomField],
"customText": [CustomText],
"domains": [Domain],
"publishedFiles": [PublishedFile],
"locations": [Location],
"modules": [Module],
"orgUnits": [OrgUnit],
"ruleClasses": [RuleClass],
"travelConfigs": [TravelConfig],
"companyGroups": [CompanyGroup],
"t2OptIn": T2OptIn,
"partnerServiceVendors": [PartnerServiceVendor]
      }
    ]
  }
}
```

Queries 

## **companiesByNameFilter** 

JWT Roles: companyadmin, travelsysadmin, sysadmin, travelagent, travelagentadmin, or travelagentnonbillable 

Response 

Returns a `Companies` 

Arguments 

Name Description 

`nameFilter` - `String!` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

24/246 

4/6/26, 2:27 PM 

config-api reference 

Description 

|||
|---|---|
|Name|Description|
|`limit`-`Int`|Default =`10`|
|`offset`-`Int`|Default =`0`|



`moduleCode` - `String` 

## **QUERY** 

```
query CompaniesByNameFilter(
$nameFilter: String!,
$limit: Int,
$offset: Int,
$moduleCode: String
){
companiesByNameFilter(
    nameFilter: $nameFilter,
    limit: $limit,
    offset: $offset,
    moduleCode: $moduleCode
  ){
pageInfo {
hasNextPage
hasPreviousPage
    }
companies {
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
...MigrationFragment
      }
directBillContractReferenceId
customFields {
...CustomFieldFragment
      }
customText {
...CustomTextFragment
      }
domains {
...DomainFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

25/246 

4/6/26, 2:27 PM 

config-api reference 

```
publishedFiles {
...PublishedFileFragment
      }
locations {
...LocationFragment
      }
modules {
...ModuleFragment
      }
orgUnits {
...OrgUnitFragment
      }
ruleClasses {
...RuleClassFragment
      }
travelConfigs {
...TravelConfigFragment
      }
companyGroups {
...CompanyGroupFragment
      }
t2OptIn {
...T2OptInFragment
      }
partnerServiceVendors {
...PartnerServiceVendorFragment
      }
    }
  }
}
```

## **VARIABLES** 

```
{
"nameFilter": "xyz789",
"limit": 10,
"offset": 0,
"moduleCode": "abc123"
}
```

## **RESPONSE** 

```
{
"data": {
"companiesByNameFilter": {
"pageInfo": PageInfo,
"companies": [Company]
    }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

26/246 

4/6/26, 2:27 PM 

config-api reference 

```
}
```

Queries 

## **companiesByTravelConfigFilter** 

Retrieves companies that have at least one travel config matching the provided filter JWT Roles: companyadmin, travelsysadmin, sysadmin 

Response Returns a `Companies` 

Arguments Name Description `filter` - `TravelConfigFilter! limit` - `Int` Default = `100 offset` - `Int` Default = `0` 

## **QUERY** 

```
query CompaniesByTravelConfigFilter(
$filter: TravelConfigFilter!,
$limit: Int,
$offset: Int
){
companiesByTravelConfigFilter(
    filter: $filter,
    limit: $limit,
    offset: $offset
  ){
pageInfo {
hasNextPage
hasPreviousPage
    }
companies {
id
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

27/246 

4/6/26, 2:27 PM 

config-api reference 

```
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
...MigrationFragment
      }
directBillContractReferenceId
customFields {
...CustomFieldFragment
      }
customText {
...CustomTextFragment
      }
domains {
...DomainFragment
      }
publishedFiles {
...PublishedFileFragment
      }
locations {
...LocationFragment
      }
modules {
...ModuleFragment
      }
orgUnits {
...OrgUnitFragment
      }
ruleClasses {
...RuleClassFragment
      }
travelConfigs {
...TravelConfigFragment
      }
companyGroups {
...CompanyGroupFragment
      }
t2OptIn {
...T2OptInFragment
      }
partnerServiceVendors {
...PartnerServiceVendorFragment
      }
    }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

28/246 

4/6/26, 2:27 PM 

config-api reference 

```
  }
}
```

## **VARIABLES** 

```
{"filter": TravelConfigFilter, "limit": 100, "offset": 0}
```

## **RESPONSE** 

```
{
"data": {
"companiesByTravelConfigFilter": {
"pageInfo": PageInfo,
"companies": [Company]
    }
  }
}
```

Queries 

## **company** 

Looks up a company using user specified in a JWT. UI safe JWT Roles: traveluser or cesuser 

Response 

Returns a `Company` 

## **QUERY** 

```
query Company {
company {
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

29/246 

4/6/26, 2:27 PM 

config-api reference 

```
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
migrationReadyUtc
migratedElsewhere
    }
directBillContractReferenceId
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
customText {
fieldName
languageCode
value
useDefault
    }
domains {
name
companyId
isDefault
    }
publishedFiles {
fileId
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

30/246 

4/6/26, 2:27 PM 

config-api reference 

```
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
locations {
id
uuid
companyId
name
address
city
state
zipCode
countryCode
latitude
longitude
allowDelivery
vendors {
...LocationVendorFragment
      }
    }
modules {
companyId
moduleCode
isActive
moduleProperties {
...ModulePropertyFragment
      }
    }
orgUnits {
orgUnitId
uuid
orgUnitName
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

31/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
travelConfigs {
id
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
...PublishedFileFragment
      }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
...AgencyConfigFragment
      }
company {
...CompanyFragment
      }
configurationItems {
...ConfigurationItemFragment
      }
configurationItemsHistory {
...ConfigurationItemFragment
      }
consortiumHotels {
...ConsortiumHotelFragment
      }
contractHotels {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

32/246 

4/6/26, 2:27 PM 

config-api reference 

```
...ContractHotelFragment
      }
customFields {
...CustomFieldFragment
      }
eReceipt {
...EReceiptFragment
      }
emailOptions {
...EmailOptionsFragment
      }
formOfPayment {
...FormOfPaymentFragment
      }
hotelSearch {
...HotelSearchFragment
      }
pnrFinishing {
...PnrFinishingFragment
      }
profileOptions {
...ProfileOptionsFragment
      }
wizardOptions {
...WizardOptionsFragment
      }
domains {
...TravelConfigDomainFragment
      }
travelConfigItems {
...TravelConfigItemFragment
      }
tsaSecureFlight {
...TsaSecureFlightFragment
      }
profileSyncOptions {
...ProfileSyncOptionsFragment
      }
vendorDiscounts {
...VendorDiscountFragment
      }
vendorExclusions {
...VendorExclusionFragment
      }
violationReasons {
...ViolationReasonFragment
      }
gdsPnr {
...GdsPnrFragment
      }
bookingSourceOptions {
...BookingSourceOptionFragment
      }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

33/246 

4/6/26, 2:27 PM 

config-api reference 

```
hotelShop {
...HotelShopFragment
      }
customText {
...CustomTextFragment
      }
carSearch {
...CarSearchFragment
      }
sharedCustomFields {
...SharedCustomFieldFragment
      }
tripOptions {
...TripOptionsFragment
      }
currencyCode
policyOptions {
...PolicyOptionsFragment
      }
airSearch {
...AirSearchFragment
      }
sabreProfile {
...SabreProfileFragment
      }
airportHubs {
...AirportHubFragment
      }
t2OptIn {
...T2OptInFragment
      }
configOptions {
...ConfigurationOptionsFragment
      }
railConnector {
...RailConnectorFragment
      }
hasFutureHotelSeasonalRates
ruleClass {
...RuleClassFragment
      }
ruleClasses {
...RuleClassFragment
      }
egenciaIntegration
contractExternalReferenceId
    }
companyGroups {
groupId
groupName
uuid
    }
t2OptIn {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

34/246 

4/6/26, 2:27 PM 

config-api reference 

```
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
partnerServiceVendors {
baseUrl
domain
login
password
vendorId
vendorCode
vendorName
vendorLogo
microserviceUrl
apiVersion
billingReferenceId
shortVendorName
systemRequestorId
systemRequestorIdType
vendorStatus
    }
  }
}
```

## **RESPONSE** 

```
{
"data": {
"company": {
"id": "abc123",
"companyId": 123,
"companyName": "xyz789",
"internetDomain": "xyz789",
"companyDomain": "abc123",
"countryCode": "xyz789",
"billingCurrencyCode": "abc123",
"uuid": "abc123",
"activeSwitch": 123,
"isBillable": true,
"travelOfferingCode": "abc123",
"isUatCompany": true,
"migration": Migration,
"directBillContractReferenceId": "xyz789",
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

35/246 

4/6/26, 2:27 PM 

config-api reference `"customFields": [CustomField], "customText": [CustomText], "domains": [Domain], "publishedFiles": [PublishedFile], "locations": [Location], "modules": [Module], "orgUnits": [OrgUnit], "ruleClasses": [RuleClass], "travelConfigs": [TravelConfig], "companyGroups": [CompanyGroup], "t2OptIn": T2OptIn, "partnerServiceVendors": [PartnerServiceVendor] } } }` 

Queries 

## **companyByEntityId** 

Looks up a company by Entity ID JWT Roles: companyadmin, travelsysadmin, sysadmin, travelagent, travelagentadmin, or travelagentnonbillable 

Response 

Returns a `Company` 

Arguments 

Name Description 

`entityId` - `String!` 

## **QUERY** 

```
query CompanyByEntityId($entityId: String!){
companyByEntityId(entityId: $entityId){
id
companyId
companyName
internetDomain
companyDomain
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

36/246 

4/6/26, 2:27 PM 

config-api reference 

```
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
migrationReadyUtc
migratedElsewhere
    }
directBillContractReferenceId
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
customText {
fieldName
languageCode
value
useDefault
    }
domains {
name
companyId
isDefault
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

37/246 

4/6/26, 2:27 PM 

config-api reference 

```
    }
```

```
publishedFiles {
fileId
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
locations {
id
uuid
companyId
name
address
city
state
zipCode
countryCode
latitude
longitude
allowDelivery
vendors {
...LocationVendorFragment
      }
    }
modules {
companyId
moduleCode
isActive
moduleProperties {
...ModulePropertyFragment
      }
    }
orgUnits {
orgUnitId
uuid
orgUnitName
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

38/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
travelConfigs {
id
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
...PublishedFileFragment
      }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
...AgencyConfigFragment
      }
company {
...CompanyFragment
      }
configurationItems {
...ConfigurationItemFragment
      }
configurationItemsHistory {
...ConfigurationItemFragment
      }
consortiumHotels {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

39/246 

4/6/26, 2:27 PM 

config-api reference 

```
...ConsortiumHotelFragment
      }
contractHotels {
...ContractHotelFragment
      }
customFields {
...CustomFieldFragment
      }
eReceipt {
...EReceiptFragment
      }
emailOptions {
...EmailOptionsFragment
      }
formOfPayment {
...FormOfPaymentFragment
      }
hotelSearch {
...HotelSearchFragment
      }
pnrFinishing {
...PnrFinishingFragment
      }
profileOptions {
...ProfileOptionsFragment
      }
wizardOptions {
...WizardOptionsFragment
      }
domains {
...TravelConfigDomainFragment
      }
travelConfigItems {
...TravelConfigItemFragment
      }
tsaSecureFlight {
...TsaSecureFlightFragment
      }
profileSyncOptions {
...ProfileSyncOptionsFragment
      }
vendorDiscounts {
...VendorDiscountFragment
      }
vendorExclusions {
...VendorExclusionFragment
      }
violationReasons {
...ViolationReasonFragment
      }
gdsPnr {
...GdsPnrFragment
      }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

40/246 

4/6/26, 2:27 PM 

config-api reference 

```
bookingSourceOptions {
...BookingSourceOptionFragment
      }
hotelShop {
...HotelShopFragment
      }
customText {
...CustomTextFragment
      }
carSearch {
...CarSearchFragment
      }
sharedCustomFields {
...SharedCustomFieldFragment
      }
tripOptions {
...TripOptionsFragment
      }
currencyCode
policyOptions {
...PolicyOptionsFragment
      }
airSearch {
...AirSearchFragment
      }
sabreProfile {
...SabreProfileFragment
      }
airportHubs {
...AirportHubFragment
      }
t2OptIn {
...T2OptInFragment
      }
configOptions {
...ConfigurationOptionsFragment
      }
railConnector {
...RailConnectorFragment
      }
hasFutureHotelSeasonalRates
ruleClass {
...RuleClassFragment
      }
ruleClasses {
...RuleClassFragment
      }
egenciaIntegration
contractExternalReferenceId
    }
companyGroups {
groupId
groupName
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

41/246 

4/6/26, 2:27 PM 

config-api reference 

```
uuid
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
partnerServiceVendors {
baseUrl
domain
login
password
vendorId
vendorCode
vendorName
vendorLogo
microserviceUrl
apiVersion
billingReferenceId
shortVendorName
systemRequestorId
systemRequestorIdType
vendorStatus
    }
  }
}
```

## **VARIABLES** 

```
{"entityId": "abc123"}
```

## **RESPONSE** 

```
{
"data": {
"companyByEntityId": {
"id": "abc123",
"companyId": 987,
"companyName": "xyz789",
"internetDomain": "xyz789",
"companyDomain": "abc123",
"countryCode": "abc123",
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

42/246 

4/6/26, 2:27 PM 

config-api reference 

```
"billingCurrencyCode": "abc123",
"uuid": "xyz789",
"activeSwitch": 987,
"isBillable": true,
"travelOfferingCode": "abc123",
"isUatCompany": false,
"migration": Migration,
"directBillContractReferenceId": "xyz789",
"customFields": [CustomField],
"customText": [CustomText],
"domains": [Domain],
"publishedFiles": [PublishedFile],
"locations": [Location],
"modules": [Module],
"orgUnits": [OrgUnit],
"ruleClasses": [RuleClass],
"travelConfigs": [TravelConfig],
"companyGroups": [CompanyGroup],
"t2OptIn": T2OptIn,
"partnerServiceVendors": [PartnerServiceVendor]
    }
  }
}
```

Queries 

## **companyById** 

Looks up a company by the Outtask integer id JWT Roles: companyadmin, travelsysadmin, or sysadmin 

Response 

Returns a `Company` 

Arguments 

Name Description 

`id` - `Int!` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

43/246 

4/6/26, 2:27 PM 

config-api reference 

## **QUERY** 

```
query CompanyById($id: Int!){
companyById(id: $id){
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
migrationReadyUtc
migratedElsewhere
    }
directBillContractReferenceId
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

44/246 

4/6/26, 2:27 PM 

config-api reference 

```
customText {
fieldName
languageCode
value
useDefault
    }
domains {
name
companyId
isDefault
    }
publishedFiles {
fileId
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
locations {
id
uuid
companyId
name
address
city
state
zipCode
countryCode
latitude
longitude
allowDelivery
vendors {
...LocationVendorFragment
      }
    }
modules {
companyId
moduleCode
isActive
moduleProperties {
...ModulePropertyFragment
      }
    }
orgUnits {
orgUnitId
uuid
orgUnitName
    }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

45/246 

4/6/26, 2:27 PM 

config-api reference 

```
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
travelConfigs {
id
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
...PublishedFileFragment
      }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
...AgencyConfigFragment
      }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

46/246 

4/6/26, 2:27 PM 

config-api reference 

```
company {
...CompanyFragment
      }
configurationItems {
...ConfigurationItemFragment
      }
configurationItemsHistory {
...ConfigurationItemFragment
      }
consortiumHotels {
...ConsortiumHotelFragment
      }
contractHotels {
...ContractHotelFragment
      }
customFields {
...CustomFieldFragment
      }
eReceipt {
...EReceiptFragment
      }
emailOptions {
...EmailOptionsFragment
      }
formOfPayment {
...FormOfPaymentFragment
      }
hotelSearch {
...HotelSearchFragment
      }
pnrFinishing {
...PnrFinishingFragment
      }
profileOptions {
...ProfileOptionsFragment
      }
wizardOptions {
...WizardOptionsFragment
      }
domains {
...TravelConfigDomainFragment
      }
travelConfigItems {
...TravelConfigItemFragment
      }
tsaSecureFlight {
...TsaSecureFlightFragment
      }
profileSyncOptions {
...ProfileSyncOptionsFragment
      }
vendorDiscounts {
...VendorDiscountFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

47/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
vendorExclusions {
...VendorExclusionFragment
      }
violationReasons {
...ViolationReasonFragment
      }
gdsPnr {
...GdsPnrFragment
      }
bookingSourceOptions {
...BookingSourceOptionFragment
      }
hotelShop {
...HotelShopFragment
      }
customText {
...CustomTextFragment
      }
carSearch {
...CarSearchFragment
      }
sharedCustomFields {
...SharedCustomFieldFragment
      }
tripOptions {
...TripOptionsFragment
      }
currencyCode
policyOptions {
...PolicyOptionsFragment
      }
airSearch {
...AirSearchFragment
      }
sabreProfile {
...SabreProfileFragment
      }
airportHubs {
...AirportHubFragment
      }
t2OptIn {
...T2OptInFragment
      }
configOptions {
...ConfigurationOptionsFragment
      }
railConnector {
...RailConnectorFragment
      }
hasFutureHotelSeasonalRates
ruleClass {
...RuleClassFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

48/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
ruleClasses {
...RuleClassFragment
      }
egenciaIntegration
contractExternalReferenceId
    }
companyGroups {
groupId
groupName
uuid
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
partnerServiceVendors {
baseUrl
domain
login
password
vendorId
vendorCode
vendorName
vendorLogo
microserviceUrl
apiVersion
billingReferenceId
shortVendorName
systemRequestorId
systemRequestorIdType
vendorStatus
    }
  }
}
```

## **VARIABLES** 

```
{"id": 987}
```

## **RESPONSE** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

49/246 

4/6/26, 2:27 PM 

config-api reference 

```
{
```

```
"data": {
"companyById": {
"id": "abc123",
"companyId": 987,
"companyName": "abc123",
"internetDomain": "abc123",
"companyDomain": "xyz789",
"countryCode": "abc123",
"billingCurrencyCode": "xyz789",
"uuid": "xyz789",
"activeSwitch": 987,
"isBillable": true,
"travelOfferingCode": "xyz789",
"isUatCompany": false,
"migration": Migration,
"directBillContractReferenceId": "xyz789",
"customFields": [CustomField],
"customText": [CustomText],
"domains": [Domain],
"publishedFiles": [PublishedFile],
"locations": [Location],
"modules": [Module],
"orgUnits": [OrgUnit],
"ruleClasses": [RuleClass],
"travelConfigs": [TravelConfig],
"companyGroups": [CompanyGroup],
"t2OptIn": T2OptIn,
"partnerServiceVendors": [PartnerServiceVendor]
    }
  }
}
```

Queries 

## **companyByUser** 

Looks up the company the given user uuid belongs to JWT Roles: companyadmin, travelsysadmin, or sysadmin 

Response 

Returns a `Company` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

50/246 

4/6/26, 2:27 PM 

config-api reference 

Arguments 

Name 

`uuid` - `String!` 

Description A users UUID 

## **QUERY** 

```
query CompanyByUser($uuid: String!){
companyByUser(uuid: $uuid){
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
migrationReadyUtc
migratedElsewhere
    }
directBillContractReferenceId
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

51/246 

4/6/26, 2:27 PM 

config-api reference 

```
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
customText {
fieldName
languageCode
value
useDefault
    }
domains {
name
companyId
isDefault
    }
publishedFiles {
fileId
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
locations {
id
uuid
companyId
name
address
city
state
zipCode
countryCode
latitude
longitude
allowDelivery
vendors {
...LocationVendorFragment
      }
    }
modules {
companyId
moduleCode
isActive
moduleProperties {
...ModulePropertyFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

52/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
    }
orgUnits {
orgUnitId
uuid
orgUnitName
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
travelConfigs {
id
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
...PublishedFileFragment
      }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

53/246 

4/6/26, 2:27 PM 

config-api reference 

```
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
...AgencyConfigFragment
      }
company {
...CompanyFragment
      }
configurationItems {
...ConfigurationItemFragment
      }
configurationItemsHistory {
...ConfigurationItemFragment
      }
consortiumHotels {
...ConsortiumHotelFragment
      }
contractHotels {
...ContractHotelFragment
      }
customFields {
...CustomFieldFragment
      }
eReceipt {
...EReceiptFragment
      }
emailOptions {
...EmailOptionsFragment
      }
formOfPayment {
...FormOfPaymentFragment
      }
hotelSearch {
...HotelSearchFragment
      }
pnrFinishing {
...PnrFinishingFragment
      }
profileOptions {
...ProfileOptionsFragment
      }
wizardOptions {
...WizardOptionsFragment
      }
domains {
...TravelConfigDomainFragment
      }
travelConfigItems {
...TravelConfigItemFragment
      }
tsaSecureFlight {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

54/246 

4/6/26, 2:27 PM 

config-api reference 

```
...TsaSecureFlightFragment
      }
profileSyncOptions {
...ProfileSyncOptionsFragment
      }
vendorDiscounts {
...VendorDiscountFragment
      }
vendorExclusions {
...VendorExclusionFragment
      }
violationReasons {
...ViolationReasonFragment
      }
gdsPnr {
...GdsPnrFragment
      }
bookingSourceOptions {
...BookingSourceOptionFragment
      }
hotelShop {
...HotelShopFragment
      }
customText {
...CustomTextFragment
      }
carSearch {
...CarSearchFragment
      }
sharedCustomFields {
...SharedCustomFieldFragment
      }
tripOptions {
...TripOptionsFragment
      }
currencyCode
policyOptions {
...PolicyOptionsFragment
      }
airSearch {
...AirSearchFragment
      }
sabreProfile {
...SabreProfileFragment
      }
airportHubs {
...AirportHubFragment
      }
t2OptIn {
...T2OptInFragment
      }
configOptions {
...ConfigurationOptionsFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

55/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
railConnector {
...RailConnectorFragment
      }
hasFutureHotelSeasonalRates
ruleClass {
...RuleClassFragment
      }
ruleClasses {
...RuleClassFragment
      }
egenciaIntegration
contractExternalReferenceId
    }
companyGroups {
groupId
groupName
uuid
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
partnerServiceVendors {
baseUrl
domain
login
password
vendorId
vendorCode
vendorName
vendorLogo
microserviceUrl
apiVersion
billingReferenceId
shortVendorName
systemRequestorId
systemRequestorIdType
vendorStatus
    }
  }
}
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

56/246 

4/6/26, 2:27 PM 

config-api reference 

## **VARIABLES** 

```
{"uuid": "abc123"}
```

**RESPONSE** 

```
{
"data": {
"companyByUser": {
"id": "abc123",
"companyId": 987,
"companyName": "xyz789",
"internetDomain": "xyz789",
"companyDomain": "xyz789",
"countryCode": "abc123",
"billingCurrencyCode": "xyz789",
"uuid": "abc123",
"activeSwitch": 987,
"isBillable": true,
"travelOfferingCode": "abc123",
"isUatCompany": false,
"migration": Migration,
"directBillContractReferenceId": "abc123",
"customFields": [CustomField],
"customText": [CustomText],
"domains": [Domain],
"publishedFiles": [PublishedFile],
"locations": [Location],
"modules": [Module],
"orgUnits": [OrgUnit],
"ruleClasses": [RuleClass],
"travelConfigs": [TravelConfig],
"companyGroups": [CompanyGroup],
"t2OptIn": T2OptIn,
"partnerServiceVendors": [PartnerServiceVendor]
    }
  }
}
```

Queries 

## **companyByUuid** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

57/246 

4/6/26, 2:27 PM 

config-api reference 

Looks up a company by UUID JWT Roles: companyadmin, travelsysadmin, sysadmin, travelagent, travelagentadmin, or travelagentnonbillable 

Response 

Returns a `Company` 

Arguments 

Name Description 

`uuid` - `String!` 

## **QUERY** 

```
query CompanyByUuid($uuid: String!){
companyByUuid(uuid: $uuid){
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
migrationReadyUtc
migratedElsewhere
    }
directBillContractReferenceId
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

58/246 

4/6/26, 2:27 PM 

config-api reference 

```
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
customText {
fieldName
languageCode
value
useDefault
    }
domains {
name
companyId
isDefault
    }
publishedFiles {
fileId
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
locations {
id
uuid
companyId
name
address
city
state
zipCode
countryCode
latitude
longitude
allowDelivery
vendors {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

59/246 

4/6/26, 2:27 PM 

config-api reference 

```
...LocationVendorFragment
      }
    }
modules {
companyId
moduleCode
isActive
moduleProperties {
...ModulePropertyFragment
      }
    }
orgUnits {
orgUnitId
uuid
orgUnitName
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
travelConfigs {
id
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
...PublishedFileFragment
      }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

60/246 

4/6/26, 2:27 PM 

config-api reference 

```
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
...AgencyConfigFragment
      }
company {
...CompanyFragment
      }
configurationItems {
...ConfigurationItemFragment
      }
configurationItemsHistory {
...ConfigurationItemFragment
      }
consortiumHotels {
...ConsortiumHotelFragment
      }
contractHotels {
...ContractHotelFragment
      }
customFields {
...CustomFieldFragment
      }
eReceipt {
...EReceiptFragment
      }
emailOptions {
...EmailOptionsFragment
      }
formOfPayment {
...FormOfPaymentFragment
      }
hotelSearch {
...HotelSearchFragment
      }
pnrFinishing {
...PnrFinishingFragment
      }
profileOptions {
...ProfileOptionsFragment
      }
wizardOptions {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

61/246 

4/6/26, 2:27 PM 

config-api reference 

```
...WizardOptionsFragment
      }
domains {
...TravelConfigDomainFragment
      }
travelConfigItems {
...TravelConfigItemFragment
      }
tsaSecureFlight {
...TsaSecureFlightFragment
      }
profileSyncOptions {
...ProfileSyncOptionsFragment
      }
vendorDiscounts {
...VendorDiscountFragment
      }
vendorExclusions {
...VendorExclusionFragment
      }
violationReasons {
...ViolationReasonFragment
      }
gdsPnr {
...GdsPnrFragment
      }
bookingSourceOptions {
...BookingSourceOptionFragment
      }
hotelShop {
...HotelShopFragment
      }
customText {
...CustomTextFragment
      }
carSearch {
...CarSearchFragment
      }
sharedCustomFields {
...SharedCustomFieldFragment
      }
tripOptions {
...TripOptionsFragment
      }
currencyCode
policyOptions {
...PolicyOptionsFragment
      }
airSearch {
...AirSearchFragment
      }
sabreProfile {
...SabreProfileFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

62/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
airportHubs {
...AirportHubFragment
      }
t2OptIn {
...T2OptInFragment
      }
configOptions {
...ConfigurationOptionsFragment
      }
railConnector {
...RailConnectorFragment
      }
hasFutureHotelSeasonalRates
ruleClass {
...RuleClassFragment
      }
ruleClasses {
...RuleClassFragment
      }
egenciaIntegration
contractExternalReferenceId
    }
companyGroups {
groupId
groupName
uuid
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
partnerServiceVendors {
baseUrl
domain
login
password
vendorId
vendorCode
vendorName
vendorLogo
microserviceUrl
apiVersion
billingReferenceId
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

63/246 

4/6/26, 2:27 PM 

config-api reference 

```
shortVendorName
systemRequestorId
systemRequestorIdType
vendorStatus
    }
  }
}
```

**VARIABLES** 

```
{"uuid": "xyz789"}
```

**RESPONSE** `{ "data": { "companyByUuid": { "id": "abc123", "companyId": 123, "companyName": "xyz789", "internetDomain": "xyz789", "companyDomain": "abc123", "countryCode": "xyz789", "billingCurrencyCode": "xyz789", "uuid": "abc123", "activeSwitch": 987, "isBillable": false, "travelOfferingCode": "xyz789", "isUatCompany": false, "migration": Migration, "directBillContractReferenceId": "xyz789", "customFields": [CustomField], "customText": [CustomText], "domains": [Domain], "publishedFiles": [PublishedFile], "locations": [Location], "modules": [Module], "orgUnits": [OrgUnit], "ruleClasses": [RuleClass], "travelConfigs": [TravelConfig], "companyGroups": [CompanyGroup], "t2OptIn": T2OptIn, "partnerServiceVendors": [PartnerServiceVendor] } } }` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

64/246 

4/6/26, 2:27 PM 

config-api reference 

Queries 

## **customFieldById** 

Response 

Returns a `CustomField` 

Arguments 

Name Description 

`id` - `Int!` 

## **QUERY** 

```
query CustomFieldById($id: Int!){
customFieldById(id: $id){
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
id
order
value
text
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

65/246 

4/6/26, 2:27 PM 

config-api reference 

```
    }
dependsOnField {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
  }
}
```

## **VARIABLES** 

```
{"id": 987}
```

## **RESPONSE** 

```
{
"data": {
"customFieldById": {
"uuid": "abc123",
"id": "abc123",
"attributeId": 987,
"attributeType": "xyz789",
"name": "xyz789",
"dataType": "xyz789",
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

66/246 

4/6/26, 2:27 PM 

config-api reference `"required": false, "minLength": 987, "maxLength": 987, "displayOnItinerary": false, "displayTitle": "xyz789", "displayAtStart": true, "displayAtEnd": true, "sort": 123, "totalValues": 987, "dependencyFieldId": "abc123", "dependencyFieldUuid": "xyz789", "dependencyValues": ["abc123"], "dependencyType": "xyz789", "displayForGuestBooking": false, "displayForRegularTrips": true, "displayForTripEdits": true, "displayForMeetings": true, "customFieldValues": [CustomFieldValue], "dependsOnField": CustomField } } }` 

Queries 

## **customFieldsByRuleClassId** 

Response 

Returns `[CustomField]` 

Arguments 

Name 

Description 

`id` - `Int!` 

## **QUERY** 

```
query CustomFieldsByRuleClassId($id: Int!){
customFieldsByRuleClassId(id: $id){
uuid
id
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

67/246 

4/6/26, 2:27 PM 

config-api reference 

```
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
id
order
value
text
    }
dependsOnField {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

68/246 

4/6/26, 2:27 PM 

config-api reference 

`} dependsOnField { ...CustomFieldFragment } } } }` **VARIABLES** `{"id": 123}` **RESPONSE** `{ "data": { "customFieldsByRuleClassId": [ { "uuid": "abc123", "id": "xyz789", "attributeId": 123, "attributeType": "abc123", "name": "xyz789", "dataType": "abc123", "required": false, "minLength": 987, "maxLength": 123, "displayOnItinerary": false, "displayTitle": "xyz789", "displayAtStart": true, "displayAtEnd": false, "sort": 987, "totalValues": 123, "dependencyFieldId": "xyz789", "dependencyFieldUuid": "abc123", "dependencyValues": ["xyz789"], "dependencyType": "xyz789", "displayForGuestBooking": true, "displayForRegularTrips": false, "displayForTripEdits": true, "displayForMeetings": false, "customFieldValues": [CustomFieldValue], "dependsOnField": CustomField } ] } }` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

69/246 

4/6/26, 2:27 PM 

config-api reference 

Queries 

## **customFieldsByRuleClassUuid** 

Response 

Returns `[CustomField]` 

Arguments 

Name Description `uuid` - `String!` v4 or v5 uuid 

## **QUERY** 

```
query CustomFieldsByRuleClassUuid($uuid: String!){
customFieldsByRuleClassUuid(uuid: $uuid){
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
id
order
value
text
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

70/246 

4/6/26, 2:27 PM 

config-api reference 

```
    }
dependsOnField {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
  }
}
```

## **VARIABLES** 

```
{"uuid": "xyz789"}
```

## **RESPONSE** 

```
{
"data": {
"customFieldsByRuleClassUuid": [
      {
"uuid": "abc123",
"id": "xyz789",
"attributeId": 123,
"attributeType": "xyz789",
"name": "xyz789",
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

71/246 

4/6/26, 2:27 PM 

config-api reference 

```
"dataType": "abc123",
"required": true,
"minLength": 123,
"maxLength": 123,
"displayOnItinerary": false,
"displayTitle": "xyz789",
"displayAtStart": true,
"displayAtEnd": true,
"sort": 123,
"totalValues": 123,
"dependencyFieldId": "abc123",
"dependencyFieldUuid": "xyz789",
"dependencyValues": ["xyz789"],
"dependencyType": "xyz789",
"displayForGuestBooking": true,
"displayForRegularTrips": false,
"displayForTripEdits": true,
"displayForMeetings": true,
"customFieldValues": [CustomFieldValue],
"dependsOnField": CustomField
      }
    ]
  }
}
```

Queries 

## **modulesByRuleClassId** 

Response 

Returns `[Module]` 

Arguments 

Name Description `id` - `Int! moduleCode` - `[String]` 

## **QUERY** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

72/246 

4/6/26, 2:27 PM 

config-api reference 

```
query ModulesByRuleClassId(
$id: Int!,
$moduleCode: [String]
){
modulesByRuleClassId(
    id: $id,
    moduleCode: $moduleCode
  ){
companyId
moduleCode
isActive
moduleProperties {
propertyId
moduleCode
propertyName
propertyValue
defaultValue
isCompanyProperty
    }
  }
}
```

## **VARIABLES** 

```
{"id": 987, "moduleCode": ["xyz789"]}
```

## **RESPONSE** 

```
{
"data": {
"modulesByRuleClassId": [
      {
"companyId": 987,
"moduleCode": "abc123",
"isActive": false,
"moduleProperties": [ModuleProperty]
      }
    ]
  }
}
```

Queries 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

73/246 

4/6/26, 2:27 PM 

config-api reference 

## **modulesByRuleClassUuid** 

Response 

Returns `[Module]` 

Arguments 

Name Description `uuid` - `String!` v4 (preferred) or v5 uuid 

`moduleCode` - `[String]` 

## **QUERY** 

```
query ModulesByRuleClassUuid(
$uuid: String!,
$moduleCode: [String]
){
modulesByRuleClassUuid(
    uuid: $uuid,
    moduleCode: $moduleCode
  ){
companyId
moduleCode
isActive
moduleProperties {
propertyId
moduleCode
propertyName
propertyValue
defaultValue
isCompanyProperty
    }
  }
}
```

## **VARIABLES** 

```
{
"uuid": "xyz789",
"moduleCode": ["abc123"]
}
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

74/246 

4/6/26, 2:27 PM 

config-api reference 

## **RESPONSE** 

```
{
"data": {
"modulesByRuleClassUuid": [
      {
"companyId": 987,
"moduleCode": "abc123",
"isActive": true,
"moduleProperties": [ModuleProperty]
      }
    ]
  }
}
```

Queries 

## **publishedFileData** 

When version is not defined will return the maximum version of the Published File 

Response 

Returns a `PublishedFileData` 

Arguments 

Name Description 

`fileId` - `Int!` 

`version` - `Int` 

## **QUERY** 

```
query PublishedFileData(
$fileId: Int!,
$version: Int
){
publishedFileData(
    fileId: $fileId,
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

75/246 

4/6/26, 2:27 PM 

config-api reference 

`version: $version ) { fileDataId fileId updatedAtUtc updatedBy version fileData } }` **VARIABLES** `{"fileId": 987, "version": 123}` **RESPONSE** `{ "data": { "publishedFileData": { "fileDataId": 123, "fileId": 987, "updatedAtUtc": "2007-12-03T10:15:30Z", "updatedBy": 123, "version": 123, "fileData": "xyz789" } } }` 

Queries 

## **ruleClasses** 

**Deprecated** Prefer travel policy service for this data 

Response 

Returns a `RuleClass` 

Arguments 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

76/246 

4/6/26, 2:27 PM 

config-api reference 

Description 

Name 

`uuid` - `String!` 

v4 (preferred) or v5 uuid 

## **QUERY** 

```
query RuleClasses($uuid: String!){
ruleClasses(uuid: $uuid){
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
managers
approvers
    }
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
ruleValues {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

77/246 

4/6/26, 2:27 PM 

config-api reference 

```
ruleValuesXml
ruleGroup
violationType
ruleValueUuid
andOperator
    }
itineraryRulesCustomFieldCount
  }
}
```

## **VARIABLES** 

```
{"uuid": "abc123"}
```

## **RESPONSE** 

```
{
"data": {
"ruleClasses": {
"id": "xyz789",
"ruleClassId": 123,
"ruleClassUuid": "abc123",
"ruleClassName": "abc123",
"propertyConfigId": 123,
"allowLimo": true,
"enableUserSuppliedHotels": true,
"approval": Approval,
"customFields": [CustomField],
"ruleValues": [RuleValue],
"itineraryRulesCustomFieldCount": 987
    }
  }
}
```

Queries 

## **travelConfig** 

Looks up a travel config using the user specified in a JWT. UI safe JWT Roles: traveluser or cesuser 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

78/246 

4/6/26, 2:27 PM 

config-api reference 

Response 

## Returns a `TravelConfig` 

**QUERY** 

```
query TravelConfig {
travelConfig {
id
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
fileId
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
uuid
agencyName
agencyNumber
finisherProblemContact
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

79/246 

4/6/26, 2:27 PM 

config-api reference 

```
address
companyId
daytimePhone
isActive
gdsType
gdsTypeName
nightPhone
pcc
profilePcc
ticketingPcc
ticketingTimeDeadline
vendorId
vendorName
wsAccessPoint
logo
daytimeHourStart
daytimeHourEnd
daytimeMessage
nightHourStart
nightHourEnd
nightMessage
virtualPaymentEnabled
fax
timeZone
agentId
sabreCreateContentCSLIUR
altAgentPcc
altAgentId
altAgentPassword
gdsPassword
altGdsPassword
agencyQueueConfigs {
...AgencyQueueConfigFragment
      }
agencyCancelPassiveSetting
agencyCancelTicketedSetting
inMaintenanceMode
    }
company {
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
...MigrationFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

80/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
```

```
directBillContractReferenceId
customFields {
...CustomFieldFragment
      }
customText {
...CustomTextFragment
      }
domains {
...DomainFragment
      }
publishedFiles {
...PublishedFileFragment
      }
locations {
...LocationFragment
      }
modules {
...ModuleFragment
      }
orgUnits {
...OrgUnitFragment
      }
ruleClasses {
...RuleClassFragment
      }
travelConfigs {
...TravelConfigFragment
      }
companyGroups {
...CompanyGroupFragment
      }
t2OptIn {
...T2OptInFragment
      }
partnerServiceVendors {
...PartnerServiceVendorFragment
      }
    }
configurationItems {
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
configurationItemsHistory {
domain
category
item
value
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

81/246 

4/6/26, 2:27 PM 

config-api reference 

```
lastModifiedBy
lastModifiedUtc
companyUuid
    }
consortiumHotels {
discountCode
refName
    }
contractHotels {
chainCode
cdNumber
contractData
propertyId
contractRate
hotelRefName
hotelPrefRank
notes
currencyCode
countryCode
propertyInfo {
...PropertyInfoFragment
      }
seasonalRates {
...ContractHotelSeasonalRatesFragment
      }
    }
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

82/246 

4/6/26, 2:27 PM 

config-api reference 

```
dependsOnField {
...CustomFieldFragment
      }
    }
eReceipt {
enableEreceipts
allowCliqbookItineraryForAirEreceipt
    }
emailOptions {
confirmationEmails
cancellationEmailSetting
holdReminderEmailSubject
approvalEmailOptions
    }
formOfPayment {
creditCardForAirRailRequired
govOnlyAirfareGhostCardNumber
govOnlyAirfareGhostCardType
govOnlyAirfareGhostCardExpiration
userCustomPropertyForDefaultCreditCard
enforceTempCardBinRestrictions
tempCardsHotelOnly
forceCreditCardChoice
showPersonalCardsBeforeGhostCards
    }
hotelSearch {
hotelMaxResults
preferredPropSearchRadius
companyLocationsSearchRadius
defaultHotelSearchRadius
hotelsWithDepositPermission
hotelDisplaysPerDiemRate
overrideBookingIataHotel
hotelSortDefault
hotelRateSortDefault
customHotelSortPrimary
customHotelSortSecondary
customHotelSortTertiary
    }
pnrFinishing {
forceFinishingBeforeApproval
ticketOption
finishingTemplate {
...PublishedFileFragment
      }
addAllBrokenRulesToFinisher
    }
profileOptions {
requirePassportInfo
    }
wizardOptions {
showGovHotel
allowAddAirFfToCarHotel
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

83/246 

4/6/26, 2:27 PM 

config-api reference 

```
cteTravelRequest
cteTravelRequestType
cteBookingSwitch
allowAddAirToExistingItin
serviceClassDefaultLowest
llfWindowSource
captureLlfFlifo
llfScreenShowWhen
llfScreenShowFlights
enableChurnDetection
churnAirlines
enableDuplicateDetection
dupDetectionAirlines
showMorningAfternoonEveningOptions
limitFarelistLlfWindow
showCommentsToAgentBox
showAgentCommentsWarning
maxCompanions
defaultDepartureHour
defaultReturnHour
mixedCarriersSplitMode
segmentFeesEnabled
fastTrackEnabled
    }
domains {
domainCode
name
nameMsgId
categories {
...TravelConfigCategoryFragment
      }
    }
travelConfigItems {
domainCode
categoryCode
itemCode
defaultItemValue
enabled
mustBeEncrypted
travelConfigUuid
itemValue
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
tsaSecureFlight {
enforceSecureFlight
sendTsaData
allowBookingWithoutDob
writeMiddleNameToPnr
    }
profileSyncOptions {
xmlSyncIdDefault
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

84/246 

4/6/26, 2:27 PM 

config-api reference 

```
gdsProfiles
gdsReadProfiles
syncBeforeSearch
    }
vendorDiscounts {
chainCode
isPreferred
extraData
prefRank
discountCode
travelCompanyType
airDiscountType
isCorporateRateOnlySearch
discountLevel
payAsYouFlyCode
promoCode
airMoreFaresBics
isRail
discountFlags {
...DiscountFlagsFragment
      }
    }
vendorExclusions {
chainCode
    }
violationReasons {
id
companyReasonCode
violationType
description
isActive
violationReasonCodeUUID
    }
gdsPnr {
writeUserSuppliedHotelPassives
requiresGdsPassive
requiresGdsPnr
iWillBookLaterUserSuppliedOption
    }
bookingSourceOptions {
bookingSourceName
requiresGdsPassive
displayName
    }
hotelShop {
countryCode
shopGds
shopHotelService
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
customText {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

85/246 

4/6/26, 2:27 PM 

config-api reference 

```
fieldName
languageCode
value
useDefault
    }
carSearch {
carDeliveryCollectionLocationRadius
carDeliveryCollectionChains
alwaysRunCarGenShopRequest
carHomeDeliveryCollectionChains
overrideBookingIataCar
defaultCarType
carShopWithLoyaltyChains {
...CarLoyaltyVendorFragment
      }
    }
sharedCustomFields {
sharingId
attributeId
travelConfigId
nonGdsBookingSourceCode
partnerServiceVendorId
sharedAttributeId
companyId
sharedAttributeName
    }
tripOptions {
allowTripHold
maxHoldDays
maxDaysPassiveApprovalHold
autoCancelRejectedTrip
autoCancelRejectedNonAirTrip
autoCancelTripHold
autoCancelApprovalHold
allowTicketVoid
    }
currencyCode
policyOptions {
ruleClassLabel
userCanSelectRuleClass
rulesUseBaseFare
forceRuleClassSelection
allowMultipleViolationCodes
    }
airSearch {
showFlyAmericaCompliance
allowPreticketAirChange
allowPostticketAirChange
flexFaring
defaultAirSearchTimeWindowDomestic
defaultAirSearchTimeWindowInternational
llfTimeWindowDomestic
llfTimeWindowInternational
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

86/246 

4/6/26, 2:27 PM 

config-api reference 

```
minAirSearchTimeWindow
maxAirSearchTimeWindow
defaultFlexFaringToMixedClass
useDomesticAirSearchTimeWindowForIntraregional
airSortDefault
scheduleSortDefault
customAirSortPrimary
customAirSortSecondary
customAirSortTertiary
customScheduleSortPrimary
customScheduleSortSecondary
customScheduleSortTertiary
ghostCardType
airLanes {
...AirLaneFragment
      }
airConnectors {
...AirConnectorFragment
      }
hideMultisegAirOption
maxPremiumShopResults
shopAcrossPaxTypes
airGuaranteedTicketingPermissions
masterPricerOptions
alternateFareOptions {
...AlternateFareOptionsFragment
      }
mobileAirBookingEnabled
simultaneousAirContracts
    }
sabreProfile {
sabreProfileDomainId
sabreProfileTemplateId
    }
airportHubs {
hubCode
regionCityName
displayName
airportRegionId
airportCodes
airportCodesWithProperties {
...AirportHubPropertyFragment
      }
latitude
longitude
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

87/246 

4/6/26, 2:27 PM 

config-api reference 

```
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
configOptions {
leaveUnusedFQVLNumbers
    }
railConnector {
evolviEnabled
sncfEnabled
amtrakEnabled
bibeEnabled
deutscheBahnEnabled
generalEnabled
renfeEnabled
searchParamsEnabled
silverRailEnabled
trainLineEnabled
viaRailEnabled
    }
hasFutureHotelSeasonalRates
ruleClass {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

88/246 

4/6/26, 2:27 PM 

config-api reference 

```
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
egenciaIntegration
contractExternalReferenceId
  }
}
```

## **RESPONSE** 

```
{
"data": {
"travelConfig": {
"id": "xyz789",
"uuid": "abc123",
"t2Id": "abc123",
"outtaskId": "abc123",
"travelConfigName": "abc123",
"bar": "xyz789",
"profileTemplateFile": PublishedFile,
"isActive": true,
"castleEnabled": false,
"hasParent": true,
"gdsType": 987,
"countryCode": "abc123",
"accountingCode": "abc123",
"allowAddAirFfToCarHotel": false,
"allowPersonalCreditCardForHotel": true,
"allowTempCardForGuestBooking": true,
"requireCardForCarRental": false,
"agencyInvoiceFopChoice": 987,
"dontWritePassives": true,
"cteTravelRequest": true,
"cteTravelRequestType": 123,
"defaultPassiveSegments": true,
"itinMessage": "xyz789",
"offlineTripPassiveApproval": false,
"usesLegacyHotelConnector": false,
"airPlusAidaEnabled": false,
"travelToolsUrl": "xyz789",
"brandingId": 123,
"agencyConfig": AgencyConfig,
"company": Company,
"configurationItems": [ConfigurationItem],
"configurationItemsHistory": [ConfigurationItem],
"consortiumHotels": [ConsortiumHotel],
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

89/246 

4/6/26, 2:27 PM 

config-api reference 

```
"contractHotels": [ContractHotel],
"customFields": [CustomField],
"eReceipt": EReceipt,
"emailOptions": EmailOptions,
"formOfPayment": FormOfPayment,
"hotelSearch": HotelSearch,
"pnrFinishing": PnrFinishing,
"profileOptions": ProfileOptions,
"wizardOptions": WizardOptions,
"domains": [TravelConfigDomain],
"travelConfigItems": [TravelConfigItem],
"tsaSecureFlight": TsaSecureFlight,
"profileSyncOptions": ProfileSyncOptions,
"vendorDiscounts": [VendorDiscount],
"vendorExclusions": [VendorExclusion],
"violationReasons": [ViolationReason],
"gdsPnr": GdsPnr,
"bookingSourceOptions": [BookingSourceOption],
"hotelShop": [HotelShop],
"customText": [CustomText],
"carSearch": CarSearch,
"sharedCustomFields": [SharedCustomField],
"tripOptions": TripOptions,
"currencyCode": "abc123",
"policyOptions": PolicyOptions,
"airSearch": AirSearch,
"sabreProfile": SabreProfile,
"airportHubs": [AirportHub],
"t2OptIn": T2OptIn,
"configOptions": ConfigurationOptions,
"railConnector": RailConnector,
"hasFutureHotelSeasonalRates": false,
"ruleClass": RuleClass,
"ruleClasses": [RuleClass],
"egenciaIntegration": 987,
"contractExternalReferenceId": "abc123"
    }
  }
}
```

Queries 

## **travelConfigById** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

90/246 

4/6/26, 2:27 PM 

config-api reference 

Looks up a travel config using the Outtask integer id JWT Roles: companyadmin, travelsysadmin, or sysadmin 

Response 

Returns a `TravelConfig` 

Arguments 

Name Description 

`id` - `Int!` 

## **QUERY** 

```
query TravelConfigById($id: Int!){
travelConfigById(id: $id){
id
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
fileId
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

91/246 

4/6/26, 2:27 PM 

config-api reference 

```
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
uuid
agencyName
agencyNumber
finisherProblemContact
address
companyId
daytimePhone
isActive
gdsType
gdsTypeName
nightPhone
pcc
profilePcc
ticketingPcc
ticketingTimeDeadline
vendorId
vendorName
wsAccessPoint
logo
daytimeHourStart
daytimeHourEnd
daytimeMessage
nightHourStart
nightHourEnd
nightMessage
virtualPaymentEnabled
fax
timeZone
agentId
sabreCreateContentCSLIUR
altAgentPcc
altAgentId
altAgentPassword
gdsPassword
altGdsPassword
agencyQueueConfigs {
...AgencyQueueConfigFragment
      }
agencyCancelPassiveSetting
agencyCancelTicketedSetting
inMaintenanceMode
    }
company {
id
companyId
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

92/246 

4/6/26, 2:27 PM 

config-api reference 

```
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
...MigrationFragment
      }
directBillContractReferenceId
customFields {
...CustomFieldFragment
      }
customText {
...CustomTextFragment
      }
domains {
...DomainFragment
      }
publishedFiles {
...PublishedFileFragment
      }
locations {
...LocationFragment
      }
modules {
...ModuleFragment
      }
orgUnits {
...OrgUnitFragment
      }
ruleClasses {
...RuleClassFragment
      }
travelConfigs {
...TravelConfigFragment
      }
companyGroups {
...CompanyGroupFragment
      }
t2OptIn {
...T2OptInFragment
      }
partnerServiceVendors {
...PartnerServiceVendorFragment
      }
    }
configurationItems {
domain
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

93/246 

4/6/26, 2:27 PM 

config-api reference 

```
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
configurationItemsHistory {
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
consortiumHotels {
discountCode
refName
    }
contractHotels {
chainCode
cdNumber
contractData
propertyId
contractRate
hotelRefName
hotelPrefRank
notes
currencyCode
countryCode
propertyInfo {
...PropertyInfoFragment
      }
seasonalRates {
...ContractHotelSeasonalRatesFragment
      }
    }
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

94/246 

4/6/26, 2:27 PM 

config-api reference 

```
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
eReceipt {
enableEreceipts
allowCliqbookItineraryForAirEreceipt
    }
emailOptions {
confirmationEmails
cancellationEmailSetting
holdReminderEmailSubject
approvalEmailOptions
    }
formOfPayment {
creditCardForAirRailRequired
govOnlyAirfareGhostCardNumber
govOnlyAirfareGhostCardType
govOnlyAirfareGhostCardExpiration
userCustomPropertyForDefaultCreditCard
enforceTempCardBinRestrictions
tempCardsHotelOnly
forceCreditCardChoice
showPersonalCardsBeforeGhostCards
    }
hotelSearch {
hotelMaxResults
preferredPropSearchRadius
companyLocationsSearchRadius
defaultHotelSearchRadius
hotelsWithDepositPermission
hotelDisplaysPerDiemRate
overrideBookingIataHotel
hotelSortDefault
hotelRateSortDefault
customHotelSortPrimary
customHotelSortSecondary
customHotelSortTertiary
    }
pnrFinishing {
forceFinishingBeforeApproval
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

95/246 

4/6/26, 2:27 PM 

config-api reference 

```
ticketOption
finishingTemplate {
...PublishedFileFragment
      }
addAllBrokenRulesToFinisher
    }
profileOptions {
requirePassportInfo
    }
wizardOptions {
showGovHotel
allowAddAirFfToCarHotel
cteTravelRequest
cteTravelRequestType
cteBookingSwitch
allowAddAirToExistingItin
serviceClassDefaultLowest
llfWindowSource
captureLlfFlifo
llfScreenShowWhen
llfScreenShowFlights
enableChurnDetection
churnAirlines
enableDuplicateDetection
dupDetectionAirlines
showMorningAfternoonEveningOptions
limitFarelistLlfWindow
showCommentsToAgentBox
showAgentCommentsWarning
maxCompanions
defaultDepartureHour
defaultReturnHour
mixedCarriersSplitMode
segmentFeesEnabled
fastTrackEnabled
    }
domains {
domainCode
name
nameMsgId
categories {
...TravelConfigCategoryFragment
      }
    }
travelConfigItems {
domainCode
categoryCode
itemCode
defaultItemValue
enabled
mustBeEncrypted
travelConfigUuid
itemValue
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

96/246 

4/6/26, 2:27 PM 

config-api reference 

```
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
tsaSecureFlight {
enforceSecureFlight
sendTsaData
allowBookingWithoutDob
writeMiddleNameToPnr
    }
profileSyncOptions {
xmlSyncIdDefault
gdsProfiles
gdsReadProfiles
syncBeforeSearch
    }
vendorDiscounts {
chainCode
isPreferred
extraData
prefRank
discountCode
travelCompanyType
airDiscountType
isCorporateRateOnlySearch
discountLevel
payAsYouFlyCode
promoCode
airMoreFaresBics
isRail
discountFlags {
...DiscountFlagsFragment
      }
    }
vendorExclusions {
chainCode
    }
violationReasons {
id
companyReasonCode
violationType
description
isActive
violationReasonCodeUUID
    }
gdsPnr {
writeUserSuppliedHotelPassives
requiresGdsPassive
requiresGdsPnr
iWillBookLaterUserSuppliedOption
    }
bookingSourceOptions {
bookingSourceName
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

97/246 

4/6/26, 2:27 PM 

config-api reference 

```
requiresGdsPassive
displayName
    }
hotelShop {
countryCode
shopGds
shopHotelService
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
customText {
fieldName
languageCode
value
useDefault
    }
carSearch {
carDeliveryCollectionLocationRadius
carDeliveryCollectionChains
alwaysRunCarGenShopRequest
carHomeDeliveryCollectionChains
overrideBookingIataCar
defaultCarType
carShopWithLoyaltyChains {
...CarLoyaltyVendorFragment
      }
    }
sharedCustomFields {
sharingId
attributeId
travelConfigId
nonGdsBookingSourceCode
partnerServiceVendorId
sharedAttributeId
companyId
sharedAttributeName
    }
tripOptions {
allowTripHold
maxHoldDays
maxDaysPassiveApprovalHold
autoCancelRejectedTrip
autoCancelRejectedNonAirTrip
autoCancelTripHold
autoCancelApprovalHold
allowTicketVoid
    }
currencyCode
policyOptions {
ruleClassLabel
userCanSelectRuleClass
rulesUseBaseFare
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

98/246 

4/6/26, 2:27 PM 

config-api reference 

```
forceRuleClassSelection
allowMultipleViolationCodes
    }
airSearch {
showFlyAmericaCompliance
allowPreticketAirChange
allowPostticketAirChange
flexFaring
defaultAirSearchTimeWindowDomestic
defaultAirSearchTimeWindowInternational
llfTimeWindowDomestic
llfTimeWindowInternational
minAirSearchTimeWindow
maxAirSearchTimeWindow
defaultFlexFaringToMixedClass
useDomesticAirSearchTimeWindowForIntraregional
airSortDefault
scheduleSortDefault
customAirSortPrimary
customAirSortSecondary
customAirSortTertiary
customScheduleSortPrimary
customScheduleSortSecondary
customScheduleSortTertiary
ghostCardType
airLanes {
...AirLaneFragment
      }
airConnectors {
...AirConnectorFragment
      }
hideMultisegAirOption
maxPremiumShopResults
shopAcrossPaxTypes
airGuaranteedTicketingPermissions
masterPricerOptions
alternateFareOptions {
...AlternateFareOptionsFragment
      }
mobileAirBookingEnabled
simultaneousAirContracts
    }
sabreProfile {
sabreProfileDomainId
sabreProfileTemplateId
    }
airportHubs {
hubCode
regionCityName
displayName
airportRegionId
airportCodes
airportCodesWithProperties {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

99/246 

4/6/26, 2:27 PM 

config-api reference 

```
...AirportHubPropertyFragment
      }
latitude
longitude
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
configOptions {
leaveUnusedFQVLNumbers
    }
railConnector {
evolviEnabled
sncfEnabled
amtrakEnabled
bibeEnabled
deutscheBahnEnabled
generalEnabled
renfeEnabled
searchParamsEnabled
silverRailEnabled
trainLineEnabled
viaRailEnabled
    }
hasFutureHotelSeasonalRates
ruleClass {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

100/246 

4/6/26, 2:27 PM 

config-api reference 

```
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
egenciaIntegration
contractExternalReferenceId
  }
}
```

## **VARIABLES** 

```
{"id": 123}
```

## **RESPONSE** 

```
{
"data": {
"travelConfigById": {
"id": "abc123",
"uuid": "xyz789",
"t2Id": "abc123",
"outtaskId": "abc123",
"travelConfigName": "abc123",
"bar": "abc123",
"profileTemplateFile": PublishedFile,
"isActive": true,
"castleEnabled": true,
"hasParent": false,
"gdsType": 123,
"countryCode": "xyz789",
"accountingCode": "xyz789",
"allowAddAirFfToCarHotel": false,
"allowPersonalCreditCardForHotel": true,
"allowTempCardForGuestBooking": true,
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

101/246 

4/6/26, 2:27 PM 

config-api reference 

```
"requireCardForCarRental": false,
"agencyInvoiceFopChoice": 987,
"dontWritePassives": true,
"cteTravelRequest": true,
"cteTravelRequestType": 123,
"defaultPassiveSegments": true,
"itinMessage": "xyz789",
"offlineTripPassiveApproval": false,
"usesLegacyHotelConnector": true,
"airPlusAidaEnabled": false,
"travelToolsUrl": "abc123",
"brandingId": 123,
"agencyConfig": AgencyConfig,
"company": Company,
"configurationItems": [ConfigurationItem],
"configurationItemsHistory": [ConfigurationItem],
"consortiumHotels": [ConsortiumHotel],
"contractHotels": [ContractHotel],
"customFields": [CustomField],
"eReceipt": EReceipt,
"emailOptions": EmailOptions,
"formOfPayment": FormOfPayment,
"hotelSearch": HotelSearch,
"pnrFinishing": PnrFinishing,
"profileOptions": ProfileOptions,
"wizardOptions": WizardOptions,
"domains": [TravelConfigDomain],
"travelConfigItems": [TravelConfigItem],
"tsaSecureFlight": TsaSecureFlight,
"profileSyncOptions": ProfileSyncOptions,
"vendorDiscounts": [VendorDiscount],
"vendorExclusions": [VendorExclusion],
"violationReasons": [ViolationReason],
"gdsPnr": GdsPnr,
"bookingSourceOptions": [BookingSourceOption],
"hotelShop": [HotelShop],
"customText": [CustomText],
"carSearch": CarSearch,
"sharedCustomFields": [SharedCustomField],
"tripOptions": TripOptions,
"currencyCode": "xyz789",
"policyOptions": PolicyOptions,
"airSearch": AirSearch,
"sabreProfile": SabreProfile,
"airportHubs": [AirportHub],
"t2OptIn": T2OptIn,
"configOptions": ConfigurationOptions,
"railConnector": RailConnector,
"hasFutureHotelSeasonalRates": true,
"ruleClass": RuleClass,
"ruleClasses": [RuleClass],
"egenciaIntegration": 123,
"contractExternalReferenceId": "abc123"
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

102/246 

4/6/26, 2:27 PM 

config-api reference 

```
}
```

Queries 

## **travelConfigByRuleClass** 

Looks up a travel config by rule class. UI safe JWT Roles: traveluser, or cesuser 

Response Returns a `TravelConfig` 

Arguments 

Name Description `uuid` - `String!` v4 (preferred) or v5 uuid 

**QUERY** `query TravelConfigByRuleClass($uuid: String!) { travelConfigByRuleClass(uuid: $uuid) { id uuid t2Id outtaskId travelConfigName bar profileTemplateFile { fileId companyId purpose subtype fileName fileExt contentType publishedFileData { ...PublishedFileDataFragment } }` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

103/246 

4/6/26, 2:27 PM 

config-api reference 

```
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
uuid
agencyName
agencyNumber
finisherProblemContact
address
companyId
daytimePhone
isActive
gdsType
gdsTypeName
nightPhone
pcc
profilePcc
ticketingPcc
ticketingTimeDeadline
vendorId
vendorName
wsAccessPoint
logo
daytimeHourStart
daytimeHourEnd
daytimeMessage
nightHourStart
nightHourEnd
nightMessage
virtualPaymentEnabled
fax
timeZone
agentId
sabreCreateContentCSLIUR
altAgentPcc
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

104/246 

4/6/26, 2:27 PM 

config-api reference 

```
altAgentId
altAgentPassword
gdsPassword
altGdsPassword
agencyQueueConfigs {
...AgencyQueueConfigFragment
      }
agencyCancelPassiveSetting
agencyCancelTicketedSetting
inMaintenanceMode
    }
company {
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
...MigrationFragment
      }
directBillContractReferenceId
customFields {
...CustomFieldFragment
      }
customText {
...CustomTextFragment
      }
domains {
...DomainFragment
      }
publishedFiles {
...PublishedFileFragment
      }
locations {
...LocationFragment
      }
modules {
...ModuleFragment
      }
orgUnits {
...OrgUnitFragment
      }
ruleClasses {
...RuleClassFragment
      }
travelConfigs {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

105/246 

4/6/26, 2:27 PM 

config-api reference 

```
...TravelConfigFragment
      }
companyGroups {
...CompanyGroupFragment
      }
t2OptIn {
...T2OptInFragment
      }
partnerServiceVendors {
...PartnerServiceVendorFragment
      }
    }
configurationItems {
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
configurationItemsHistory {
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
consortiumHotels {
discountCode
refName
    }
contractHotels {
chainCode
cdNumber
contractData
propertyId
contractRate
hotelRefName
hotelPrefRank
notes
currencyCode
countryCode
propertyInfo {
...PropertyInfoFragment
      }
seasonalRates {
...ContractHotelSeasonalRatesFragment
      }
    }
customFields {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

106/246 

4/6/26, 2:27 PM 

config-api reference 

```
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
eReceipt {
enableEreceipts
allowCliqbookItineraryForAirEreceipt
    }
emailOptions {
confirmationEmails
cancellationEmailSetting
holdReminderEmailSubject
approvalEmailOptions
    }
formOfPayment {
creditCardForAirRailRequired
govOnlyAirfareGhostCardNumber
govOnlyAirfareGhostCardType
govOnlyAirfareGhostCardExpiration
userCustomPropertyForDefaultCreditCard
enforceTempCardBinRestrictions
tempCardsHotelOnly
forceCreditCardChoice
showPersonalCardsBeforeGhostCards
    }
hotelSearch {
hotelMaxResults
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

107/246 

4/6/26, 2:27 PM 

config-api reference 

```
preferredPropSearchRadius
companyLocationsSearchRadius
defaultHotelSearchRadius
hotelsWithDepositPermission
hotelDisplaysPerDiemRate
overrideBookingIataHotel
hotelSortDefault
hotelRateSortDefault
customHotelSortPrimary
customHotelSortSecondary
customHotelSortTertiary
    }
pnrFinishing {
forceFinishingBeforeApproval
ticketOption
finishingTemplate {
...PublishedFileFragment
      }
addAllBrokenRulesToFinisher
    }
profileOptions {
requirePassportInfo
    }
wizardOptions {
showGovHotel
allowAddAirFfToCarHotel
cteTravelRequest
cteTravelRequestType
cteBookingSwitch
allowAddAirToExistingItin
serviceClassDefaultLowest
llfWindowSource
captureLlfFlifo
llfScreenShowWhen
llfScreenShowFlights
enableChurnDetection
churnAirlines
enableDuplicateDetection
dupDetectionAirlines
showMorningAfternoonEveningOptions
limitFarelistLlfWindow
showCommentsToAgentBox
showAgentCommentsWarning
maxCompanions
defaultDepartureHour
defaultReturnHour
mixedCarriersSplitMode
segmentFeesEnabled
fastTrackEnabled
    }
domains {
domainCode
name
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

108/246 

4/6/26, 2:27 PM 

config-api reference 

```
nameMsgId
categories {
...TravelConfigCategoryFragment
      }
    }
travelConfigItems {
domainCode
categoryCode
itemCode
defaultItemValue
enabled
mustBeEncrypted
travelConfigUuid
itemValue
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
tsaSecureFlight {
enforceSecureFlight
sendTsaData
allowBookingWithoutDob
writeMiddleNameToPnr
    }
profileSyncOptions {
xmlSyncIdDefault
gdsProfiles
gdsReadProfiles
syncBeforeSearch
    }
vendorDiscounts {
chainCode
isPreferred
extraData
prefRank
discountCode
travelCompanyType
airDiscountType
isCorporateRateOnlySearch
discountLevel
payAsYouFlyCode
promoCode
airMoreFaresBics
isRail
discountFlags {
...DiscountFlagsFragment
      }
    }
vendorExclusions {
chainCode
    }
violationReasons {
id
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

109/246 

4/6/26, 2:27 PM 

config-api reference 

```
companyReasonCode
violationType
description
isActive
violationReasonCodeUUID
    }
gdsPnr {
writeUserSuppliedHotelPassives
requiresGdsPassive
requiresGdsPnr
iWillBookLaterUserSuppliedOption
    }
bookingSourceOptions {
bookingSourceName
requiresGdsPassive
displayName
    }
hotelShop {
countryCode
shopGds
shopHotelService
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
customText {
fieldName
languageCode
value
useDefault
    }
carSearch {
carDeliveryCollectionLocationRadius
carDeliveryCollectionChains
alwaysRunCarGenShopRequest
carHomeDeliveryCollectionChains
overrideBookingIataCar
defaultCarType
carShopWithLoyaltyChains {
...CarLoyaltyVendorFragment
      }
    }
sharedCustomFields {
sharingId
attributeId
travelConfigId
nonGdsBookingSourceCode
partnerServiceVendorId
sharedAttributeId
companyId
sharedAttributeName
    }
tripOptions {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

110/246 

4/6/26, 2:27 PM 

config-api reference 

```
allowTripHold
maxHoldDays
maxDaysPassiveApprovalHold
autoCancelRejectedTrip
autoCancelRejectedNonAirTrip
autoCancelTripHold
autoCancelApprovalHold
allowTicketVoid
    }
currencyCode
policyOptions {
ruleClassLabel
userCanSelectRuleClass
rulesUseBaseFare
forceRuleClassSelection
allowMultipleViolationCodes
    }
airSearch {
showFlyAmericaCompliance
allowPreticketAirChange
allowPostticketAirChange
flexFaring
defaultAirSearchTimeWindowDomestic
defaultAirSearchTimeWindowInternational
llfTimeWindowDomestic
llfTimeWindowInternational
minAirSearchTimeWindow
maxAirSearchTimeWindow
defaultFlexFaringToMixedClass
useDomesticAirSearchTimeWindowForIntraregional
airSortDefault
scheduleSortDefault
customAirSortPrimary
customAirSortSecondary
customAirSortTertiary
customScheduleSortPrimary
customScheduleSortSecondary
customScheduleSortTertiary
ghostCardType
airLanes {
...AirLaneFragment
      }
airConnectors {
...AirConnectorFragment
      }
hideMultisegAirOption
maxPremiumShopResults
shopAcrossPaxTypes
airGuaranteedTicketingPermissions
masterPricerOptions
alternateFareOptions {
...AlternateFareOptionsFragment
      }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

111/246 

4/6/26, 2:27 PM 

config-api reference 

```
mobileAirBookingEnabled
simultaneousAirContracts
    }
sabreProfile {
sabreProfileDomainId
sabreProfileTemplateId
    }
airportHubs {
hubCode
regionCityName
displayName
airportRegionId
airportCodes
airportCodesWithProperties {
...AirportHubPropertyFragment
      }
latitude
longitude
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
configOptions {
leaveUnusedFQVLNumbers
    }
railConnector {
evolviEnabled
sncfEnabled
amtrakEnabled
bibeEnabled
deutscheBahnEnabled
generalEnabled
renfeEnabled
searchParamsEnabled
silverRailEnabled
trainLineEnabled
viaRailEnabled
    }
hasFutureHotelSeasonalRates
ruleClass {
id
ruleClassId
ruleClassUuid
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

112/246 

4/6/26, 2:27 PM 

config-api reference 

```
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
egenciaIntegration
contractExternalReferenceId
  }
}
```

## **VARIABLES** 

```
{"uuid": "abc123"}
```

## **RESPONSE** 

```
{
"data": {
"travelConfigByRuleClass": {
"id": "abc123",
"uuid": "xyz789",
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

113/246 

4/6/26, 2:27 PM 

config-api reference 

```
"t2Id": "abc123",
"outtaskId": "abc123",
"travelConfigName": "xyz789",
"bar": "xyz789",
"profileTemplateFile": PublishedFile,
"isActive": true,
"castleEnabled": true,
"hasParent": false,
"gdsType": 123,
"countryCode": "abc123",
"accountingCode": "abc123",
"allowAddAirFfToCarHotel": false,
"allowPersonalCreditCardForHotel": false,
"allowTempCardForGuestBooking": true,
"requireCardForCarRental": true,
"agencyInvoiceFopChoice": 987,
"dontWritePassives": false,
"cteTravelRequest": false,
"cteTravelRequestType": 987,
"defaultPassiveSegments": true,
"itinMessage": "xyz789",
"offlineTripPassiveApproval": false,
"usesLegacyHotelConnector": true,
"airPlusAidaEnabled": true,
"travelToolsUrl": "abc123",
"brandingId": 987,
"agencyConfig": AgencyConfig,
"company": Company,
"configurationItems": [ConfigurationItem],
"configurationItemsHistory": [ConfigurationItem],
"consortiumHotels": [ConsortiumHotel],
"contractHotels": [ContractHotel],
"customFields": [CustomField],
"eReceipt": EReceipt,
"emailOptions": EmailOptions,
"formOfPayment": FormOfPayment,
"hotelSearch": HotelSearch,
"pnrFinishing": PnrFinishing,
"profileOptions": ProfileOptions,
"wizardOptions": WizardOptions,
"domains": [TravelConfigDomain],
"travelConfigItems": [TravelConfigItem],
"tsaSecureFlight": TsaSecureFlight,
"profileSyncOptions": ProfileSyncOptions,
"vendorDiscounts": [VendorDiscount],
"vendorExclusions": [VendorExclusion],
"violationReasons": [ViolationReason],
"gdsPnr": GdsPnr,
"bookingSourceOptions": [BookingSourceOption],
"hotelShop": [HotelShop],
"customText": [CustomText],
"carSearch": CarSearch,
"sharedCustomFields": [SharedCustomField],
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

114/246 

4/6/26, 2:27 PM 

config-api reference 

```
"tripOptions": TripOptions,
"currencyCode": "xyz789",
"policyOptions": PolicyOptions,
"airSearch": AirSearch,
"sabreProfile": SabreProfile,
"airportHubs": [AirportHub],
"t2OptIn": T2OptIn,
"configOptions": ConfigurationOptions,
"railConnector": RailConnector,
"hasFutureHotelSeasonalRates": true,
"ruleClass": RuleClass,
"ruleClasses": [RuleClass],
"egenciaIntegration": 987,
"contractExternalReferenceId": "xyz789"
    }
  }
}
```

Queries 

## **travelConfigByRuleClassId** 

Looks up a travel config using the Outtask integer Rule Class id JWT Roles: traveluser, or cesuser 

Response 

Returns a `TravelConfig` 

Arguments 

Name Description 

`id` - `Int!` 

## **QUERY** 

```
query TravelConfigByRuleClassId($id: Int!){
travelConfigByRuleClassId(id: $id){
id
uuid
t2Id
outtaskId
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

115/246 

4/6/26, 2:27 PM 

config-api reference 

```
travelConfigName
bar
profileTemplateFile {
fileId
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
uuid
agencyName
agencyNumber
finisherProblemContact
address
companyId
daytimePhone
isActive
gdsType
gdsTypeName
nightPhone
pcc
profilePcc
ticketingPcc
ticketingTimeDeadline
vendorId
vendorName
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

116/246 

4/6/26, 2:27 PM 

config-api reference 

```
wsAccessPoint
logo
daytimeHourStart
daytimeHourEnd
daytimeMessage
nightHourStart
nightHourEnd
nightMessage
virtualPaymentEnabled
fax
timeZone
agentId
sabreCreateContentCSLIUR
altAgentPcc
altAgentId
altAgentPassword
gdsPassword
altGdsPassword
agencyQueueConfigs {
...AgencyQueueConfigFragment
      }
agencyCancelPassiveSetting
agencyCancelTicketedSetting
inMaintenanceMode
    }
company {
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
...MigrationFragment
      }
directBillContractReferenceId
customFields {
...CustomFieldFragment
      }
customText {
...CustomTextFragment
      }
domains {
...DomainFragment
      }
publishedFiles {
...PublishedFileFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

117/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
```

```
locations {
...LocationFragment
      }
modules {
...ModuleFragment
      }
orgUnits {
...OrgUnitFragment
      }
ruleClasses {
...RuleClassFragment
      }
travelConfigs {
...TravelConfigFragment
      }
companyGroups {
...CompanyGroupFragment
      }
t2OptIn {
...T2OptInFragment
      }
partnerServiceVendors {
...PartnerServiceVendorFragment
      }
    }
configurationItems {
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
configurationItemsHistory {
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
consortiumHotels {
discountCode
refName
    }
contractHotels {
chainCode
cdNumber
contractData
propertyId
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

118/246 

4/6/26, 2:27 PM 

config-api reference 

```
contractRate
hotelRefName
hotelPrefRank
notes
currencyCode
countryCode
propertyInfo {
...PropertyInfoFragment
      }
seasonalRates {
...ContractHotelSeasonalRatesFragment
      }
    }
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
eReceipt {
enableEreceipts
allowCliqbookItineraryForAirEreceipt
    }
emailOptions {
confirmationEmails
cancellationEmailSetting
holdReminderEmailSubject
approvalEmailOptions
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

119/246 

4/6/26, 2:27 PM 

config-api reference 

```
    }
```

```
formOfPayment {
creditCardForAirRailRequired
govOnlyAirfareGhostCardNumber
govOnlyAirfareGhostCardType
govOnlyAirfareGhostCardExpiration
userCustomPropertyForDefaultCreditCard
enforceTempCardBinRestrictions
tempCardsHotelOnly
forceCreditCardChoice
showPersonalCardsBeforeGhostCards
    }
hotelSearch {
hotelMaxResults
preferredPropSearchRadius
companyLocationsSearchRadius
defaultHotelSearchRadius
hotelsWithDepositPermission
hotelDisplaysPerDiemRate
overrideBookingIataHotel
hotelSortDefault
hotelRateSortDefault
customHotelSortPrimary
customHotelSortSecondary
customHotelSortTertiary
    }
pnrFinishing {
forceFinishingBeforeApproval
ticketOption
finishingTemplate {
...PublishedFileFragment
      }
addAllBrokenRulesToFinisher
    }
profileOptions {
requirePassportInfo
    }
wizardOptions {
showGovHotel
allowAddAirFfToCarHotel
cteTravelRequest
cteTravelRequestType
cteBookingSwitch
allowAddAirToExistingItin
serviceClassDefaultLowest
llfWindowSource
captureLlfFlifo
llfScreenShowWhen
llfScreenShowFlights
enableChurnDetection
churnAirlines
enableDuplicateDetection
dupDetectionAirlines
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

120/246 

4/6/26, 2:27 PM 

config-api reference 

```
showMorningAfternoonEveningOptions
limitFarelistLlfWindow
showCommentsToAgentBox
showAgentCommentsWarning
maxCompanions
defaultDepartureHour
defaultReturnHour
mixedCarriersSplitMode
segmentFeesEnabled
fastTrackEnabled
    }
domains {
domainCode
name
nameMsgId
categories {
...TravelConfigCategoryFragment
      }
    }
travelConfigItems {
domainCode
categoryCode
itemCode
defaultItemValue
enabled
mustBeEncrypted
travelConfigUuid
itemValue
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
tsaSecureFlight {
enforceSecureFlight
sendTsaData
allowBookingWithoutDob
writeMiddleNameToPnr
    }
profileSyncOptions {
xmlSyncIdDefault
gdsProfiles
gdsReadProfiles
syncBeforeSearch
    }
vendorDiscounts {
chainCode
isPreferred
extraData
prefRank
discountCode
travelCompanyType
airDiscountType
isCorporateRateOnlySearch
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

121/246 

4/6/26, 2:27 PM 

config-api reference 

```
discountLevel
payAsYouFlyCode
promoCode
airMoreFaresBics
isRail
discountFlags {
...DiscountFlagsFragment
      }
    }
vendorExclusions {
chainCode
    }
violationReasons {
id
companyReasonCode
violationType
description
isActive
violationReasonCodeUUID
    }
gdsPnr {
writeUserSuppliedHotelPassives
requiresGdsPassive
requiresGdsPnr
iWillBookLaterUserSuppliedOption
    }
bookingSourceOptions {
bookingSourceName
requiresGdsPassive
displayName
    }
hotelShop {
countryCode
shopGds
shopHotelService
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
customText {
fieldName
languageCode
value
useDefault
    }
carSearch {
carDeliveryCollectionLocationRadius
carDeliveryCollectionChains
alwaysRunCarGenShopRequest
carHomeDeliveryCollectionChains
overrideBookingIataCar
defaultCarType
carShopWithLoyaltyChains {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

122/246 

4/6/26, 2:27 PM 

config-api reference 

```
...CarLoyaltyVendorFragment
```

```
      }
    }
sharedCustomFields {
sharingId
attributeId
travelConfigId
nonGdsBookingSourceCode
partnerServiceVendorId
sharedAttributeId
companyId
sharedAttributeName
    }
tripOptions {
allowTripHold
maxHoldDays
maxDaysPassiveApprovalHold
autoCancelRejectedTrip
autoCancelRejectedNonAirTrip
autoCancelTripHold
autoCancelApprovalHold
allowTicketVoid
    }
currencyCode
policyOptions {
ruleClassLabel
userCanSelectRuleClass
rulesUseBaseFare
forceRuleClassSelection
allowMultipleViolationCodes
    }
airSearch {
showFlyAmericaCompliance
allowPreticketAirChange
allowPostticketAirChange
flexFaring
defaultAirSearchTimeWindowDomestic
defaultAirSearchTimeWindowInternational
llfTimeWindowDomestic
llfTimeWindowInternational
minAirSearchTimeWindow
maxAirSearchTimeWindow
defaultFlexFaringToMixedClass
useDomesticAirSearchTimeWindowForIntraregional
airSortDefault
scheduleSortDefault
customAirSortPrimary
customAirSortSecondary
customAirSortTertiary
customScheduleSortPrimary
customScheduleSortSecondary
customScheduleSortTertiary
ghostCardType
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

123/246 

4/6/26, 2:27 PM 

config-api reference 

```
airLanes {
...AirLaneFragment
      }
airConnectors {
...AirConnectorFragment
      }
hideMultisegAirOption
maxPremiumShopResults
shopAcrossPaxTypes
airGuaranteedTicketingPermissions
masterPricerOptions
alternateFareOptions {
...AlternateFareOptionsFragment
      }
mobileAirBookingEnabled
simultaneousAirContracts
    }
sabreProfile {
sabreProfileDomainId
sabreProfileTemplateId
    }
airportHubs {
hubCode
regionCityName
displayName
airportRegionId
airportCodes
airportCodesWithProperties {
...AirportHubPropertyFragment
      }
latitude
longitude
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
configOptions {
leaveUnusedFQVLNumbers
    }
railConnector {
evolviEnabled
sncfEnabled
amtrakEnabled
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

124/246 

4/6/26, 2:27 PM 

config-api reference 

```
bibeEnabled
deutscheBahnEnabled
generalEnabled
renfeEnabled
searchParamsEnabled
silverRailEnabled
trainLineEnabled
viaRailEnabled
    }
hasFutureHotelSeasonalRates
ruleClass {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
egenciaIntegration
contractExternalReferenceId
  }
}
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

125/246 

4/6/26, 2:27 PM 

config-api reference 

## **VARIABLES** 

```
{"id": 123}
```

**RESPONSE** 

```
{
"data": {
"travelConfigByRuleClassId": {
"id": "abc123",
"uuid": "xyz789",
"t2Id": "abc123",
"outtaskId": "xyz789",
"travelConfigName": "abc123",
"bar": "abc123",
"profileTemplateFile": PublishedFile,
"isActive": true,
"castleEnabled": true,
"hasParent": false,
"gdsType": 987,
"countryCode": "abc123",
"accountingCode": "xyz789",
"allowAddAirFfToCarHotel": true,
"allowPersonalCreditCardForHotel": false,
"allowTempCardForGuestBooking": false,
"requireCardForCarRental": true,
"agencyInvoiceFopChoice": 123,
"dontWritePassives": false,
"cteTravelRequest": false,
"cteTravelRequestType": 987,
"defaultPassiveSegments": true,
"itinMessage": "abc123",
"offlineTripPassiveApproval": true,
"usesLegacyHotelConnector": true,
"airPlusAidaEnabled": true,
"travelToolsUrl": "xyz789",
"brandingId": 123,
"agencyConfig": AgencyConfig,
"company": Company,
"configurationItems": [ConfigurationItem],
"configurationItemsHistory": [ConfigurationItem],
"consortiumHotels": [ConsortiumHotel],
"contractHotels": [ContractHotel],
"customFields": [CustomField],
"eReceipt": EReceipt,
"emailOptions": EmailOptions,
"formOfPayment": FormOfPayment,
"hotelSearch": HotelSearch,
"pnrFinishing": PnrFinishing,
"profileOptions": ProfileOptions,
"wizardOptions": WizardOptions,
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

126/246 

4/6/26, 2:27 PM 

config-api reference 

```
"domains": [TravelConfigDomain],
"travelConfigItems": [TravelConfigItem],
"tsaSecureFlight": TsaSecureFlight,
"profileSyncOptions": ProfileSyncOptions,
"vendorDiscounts": [VendorDiscount],
"vendorExclusions": [VendorExclusion],
"violationReasons": [ViolationReason],
"gdsPnr": GdsPnr,
"bookingSourceOptions": [BookingSourceOption],
"hotelShop": [HotelShop],
"customText": [CustomText],
"carSearch": CarSearch,
"sharedCustomFields": [SharedCustomField],
"tripOptions": TripOptions,
"currencyCode": "xyz789",
"policyOptions": PolicyOptions,
"airSearch": AirSearch,
"sabreProfile": SabreProfile,
"airportHubs": [AirportHub],
"t2OptIn": T2OptIn,
"configOptions": ConfigurationOptions,
"railConnector": RailConnector,
"hasFutureHotelSeasonalRates": false,
"ruleClass": RuleClass,
"ruleClasses": [RuleClass],
"egenciaIntegration": 987,
"contractExternalReferenceId": "xyz789"
    }
  }
}
```

Queries 

## **travelConfigByUser** 

Looks up the travel config the given user uuid belongs to JWT Roles: companyadmin, travelsysadmin, or sysadmin 

Response 

Returns a `TravelConfig` 

Arguments 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

127/246 

4/6/26, 2:27 PM 

config-api reference 

Description 

Name 

`uuid` - `String!` 

## **QUERY** 

```
query TravelConfigByUser($uuid: String!){
travelConfigByUser(uuid: $uuid){
id
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
fileId
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
uuid
agencyName
agencyNumber
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

128/246 

4/6/26, 2:27 PM 

config-api reference 

```
finisherProblemContact
address
companyId
daytimePhone
isActive
gdsType
gdsTypeName
nightPhone
pcc
profilePcc
ticketingPcc
ticketingTimeDeadline
vendorId
vendorName
wsAccessPoint
logo
daytimeHourStart
daytimeHourEnd
daytimeMessage
nightHourStart
nightHourEnd
nightMessage
virtualPaymentEnabled
fax
timeZone
agentId
sabreCreateContentCSLIUR
altAgentPcc
altAgentId
altAgentPassword
gdsPassword
altGdsPassword
agencyQueueConfigs {
...AgencyQueueConfigFragment
      }
agencyCancelPassiveSetting
agencyCancelTicketedSetting
inMaintenanceMode
    }
company {
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

129/246 

4/6/26, 2:27 PM 

config-api reference 

```
...MigrationFragment
      }
directBillContractReferenceId
customFields {
...CustomFieldFragment
      }
customText {
...CustomTextFragment
      }
domains {
...DomainFragment
      }
publishedFiles {
...PublishedFileFragment
      }
locations {
...LocationFragment
      }
modules {
...ModuleFragment
      }
orgUnits {
...OrgUnitFragment
      }
ruleClasses {
...RuleClassFragment
      }
travelConfigs {
...TravelConfigFragment
      }
companyGroups {
...CompanyGroupFragment
      }
t2OptIn {
...T2OptInFragment
      }
partnerServiceVendors {
...PartnerServiceVendorFragment
      }
    }
configurationItems {
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
configurationItemsHistory {
domain
category
item
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

130/246 

4/6/26, 2:27 PM 

config-api reference 

```
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
consortiumHotels {
discountCode
refName
    }
contractHotels {
chainCode
cdNumber
contractData
propertyId
contractRate
hotelRefName
hotelPrefRank
notes
currencyCode
countryCode
propertyInfo {
...PropertyInfoFragment
      }
seasonalRates {
...ContractHotelSeasonalRatesFragment
      }
    }
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

131/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
dependsOnField {
...CustomFieldFragment
      }
    }
eReceipt {
enableEreceipts
allowCliqbookItineraryForAirEreceipt
    }
emailOptions {
confirmationEmails
cancellationEmailSetting
holdReminderEmailSubject
approvalEmailOptions
    }
formOfPayment {
creditCardForAirRailRequired
govOnlyAirfareGhostCardNumber
govOnlyAirfareGhostCardType
govOnlyAirfareGhostCardExpiration
userCustomPropertyForDefaultCreditCard
enforceTempCardBinRestrictions
tempCardsHotelOnly
forceCreditCardChoice
showPersonalCardsBeforeGhostCards
    }
hotelSearch {
hotelMaxResults
preferredPropSearchRadius
companyLocationsSearchRadius
defaultHotelSearchRadius
hotelsWithDepositPermission
hotelDisplaysPerDiemRate
overrideBookingIataHotel
hotelSortDefault
hotelRateSortDefault
customHotelSortPrimary
customHotelSortSecondary
customHotelSortTertiary
    }
pnrFinishing {
forceFinishingBeforeApproval
ticketOption
finishingTemplate {
...PublishedFileFragment
      }
addAllBrokenRulesToFinisher
    }
profileOptions {
requirePassportInfo
    }
wizardOptions {
showGovHotel
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

132/246 

4/6/26, 2:27 PM 

config-api reference 

```
allowAddAirFfToCarHotel
cteTravelRequest
cteTravelRequestType
cteBookingSwitch
allowAddAirToExistingItin
serviceClassDefaultLowest
llfWindowSource
captureLlfFlifo
llfScreenShowWhen
llfScreenShowFlights
enableChurnDetection
churnAirlines
enableDuplicateDetection
dupDetectionAirlines
showMorningAfternoonEveningOptions
limitFarelistLlfWindow
showCommentsToAgentBox
showAgentCommentsWarning
maxCompanions
defaultDepartureHour
defaultReturnHour
mixedCarriersSplitMode
segmentFeesEnabled
fastTrackEnabled
    }
domains {
domainCode
name
nameMsgId
categories {
...TravelConfigCategoryFragment
      }
    }
travelConfigItems {
domainCode
categoryCode
itemCode
defaultItemValue
enabled
mustBeEncrypted
travelConfigUuid
itemValue
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
tsaSecureFlight {
enforceSecureFlight
sendTsaData
allowBookingWithoutDob
writeMiddleNameToPnr
    }
profileSyncOptions {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

133/246 

4/6/26, 2:27 PM 

config-api reference 

```
xmlSyncIdDefault
gdsProfiles
gdsReadProfiles
syncBeforeSearch
    }
vendorDiscounts {
chainCode
isPreferred
extraData
prefRank
discountCode
travelCompanyType
airDiscountType
isCorporateRateOnlySearch
discountLevel
payAsYouFlyCode
promoCode
airMoreFaresBics
isRail
discountFlags {
...DiscountFlagsFragment
      }
    }
vendorExclusions {
chainCode
    }
violationReasons {
id
companyReasonCode
violationType
description
isActive
violationReasonCodeUUID
    }
gdsPnr {
writeUserSuppliedHotelPassives
requiresGdsPassive
requiresGdsPnr
iWillBookLaterUserSuppliedOption
    }
bookingSourceOptions {
bookingSourceName
requiresGdsPassive
displayName
    }
hotelShop {
countryCode
shopGds
shopHotelService
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

134/246 

4/6/26, 2:27 PM 

config-api reference 

```
customText {
fieldName
languageCode
value
useDefault
    }
carSearch {
carDeliveryCollectionLocationRadius
carDeliveryCollectionChains
alwaysRunCarGenShopRequest
carHomeDeliveryCollectionChains
overrideBookingIataCar
defaultCarType
carShopWithLoyaltyChains {
...CarLoyaltyVendorFragment
      }
    }
sharedCustomFields {
sharingId
attributeId
travelConfigId
nonGdsBookingSourceCode
partnerServiceVendorId
sharedAttributeId
companyId
sharedAttributeName
    }
tripOptions {
allowTripHold
maxHoldDays
maxDaysPassiveApprovalHold
autoCancelRejectedTrip
autoCancelRejectedNonAirTrip
autoCancelTripHold
autoCancelApprovalHold
allowTicketVoid
    }
currencyCode
policyOptions {
ruleClassLabel
userCanSelectRuleClass
rulesUseBaseFare
forceRuleClassSelection
allowMultipleViolationCodes
    }
airSearch {
showFlyAmericaCompliance
allowPreticketAirChange
allowPostticketAirChange
flexFaring
defaultAirSearchTimeWindowDomestic
defaultAirSearchTimeWindowInternational
llfTimeWindowDomestic
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

135/246 

4/6/26, 2:27 PM 

config-api reference 

```
llfTimeWindowInternational
minAirSearchTimeWindow
maxAirSearchTimeWindow
defaultFlexFaringToMixedClass
useDomesticAirSearchTimeWindowForIntraregional
airSortDefault
scheduleSortDefault
customAirSortPrimary
customAirSortSecondary
customAirSortTertiary
customScheduleSortPrimary
customScheduleSortSecondary
customScheduleSortTertiary
ghostCardType
airLanes {
...AirLaneFragment
      }
airConnectors {
...AirConnectorFragment
      }
hideMultisegAirOption
maxPremiumShopResults
shopAcrossPaxTypes
airGuaranteedTicketingPermissions
masterPricerOptions
alternateFareOptions {
...AlternateFareOptionsFragment
      }
mobileAirBookingEnabled
simultaneousAirContracts
    }
sabreProfile {
sabreProfileDomainId
sabreProfileTemplateId
    }
airportHubs {
hubCode
regionCityName
displayName
airportRegionId
airportCodes
airportCodesWithProperties {
...AirportHubPropertyFragment
      }
latitude
longitude
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

136/246 

4/6/26, 2:27 PM 

config-api reference 

```
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
configOptions {
leaveUnusedFQVLNumbers
    }
railConnector {
evolviEnabled
sncfEnabled
amtrakEnabled
bibeEnabled
deutscheBahnEnabled
generalEnabled
renfeEnabled
searchParamsEnabled
silverRailEnabled
trainLineEnabled
viaRailEnabled
    }
hasFutureHotelSeasonalRates
ruleClass {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

137/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
egenciaIntegration
contractExternalReferenceId
  }
}
```

**VARIABLES** 

```
{"uuid": "abc123"}
```

**RESPONSE** `{ "data": { "travelConfigByUser": { "id": "xyz789", "uuid": "abc123", "t2Id": "abc123", "outtaskId": "abc123", "travelConfigName": "xyz789", "bar": "abc123", "profileTemplateFile": PublishedFile, "isActive": false, "castleEnabled": false, "hasParent": true, "gdsType": 987, "countryCode": "abc123", "accountingCode": "abc123", "allowAddAirFfToCarHotel": true, "allowPersonalCreditCardForHotel": false, "allowTempCardForGuestBooking": true, "requireCardForCarRental": false, "agencyInvoiceFopChoice": 987, "dontWritePassives": true, "cteTravelRequest": true, "cteTravelRequestType": 987, "defaultPassiveSegments": true, "itinMessage": "abc123", "offlineTripPassiveApproval": false, "usesLegacyHotelConnector": true, "airPlusAidaEnabled": false, "travelToolsUrl": "abc123",` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

138/246 

4/6/26, 2:27 PM 

config-api reference `"brandingId": 987, "agencyConfig": AgencyConfig, "company": Company, "configurationItems": [ConfigurationItem], "configurationItemsHistory": [ConfigurationItem], "consortiumHotels": [ConsortiumHotel], "contractHotels": [ContractHotel], "customFields": [CustomField], "eReceipt": EReceipt, "emailOptions": EmailOptions, "formOfPayment": FormOfPayment, "hotelSearch": HotelSearch, "pnrFinishing": PnrFinishing, "profileOptions": ProfileOptions, "wizardOptions": WizardOptions, "domains": [TravelConfigDomain], "travelConfigItems": [TravelConfigItem], "tsaSecureFlight": TsaSecureFlight, "profileSyncOptions": ProfileSyncOptions, "vendorDiscounts": [VendorDiscount], "vendorExclusions": [VendorExclusion], "violationReasons": [ViolationReason], "gdsPnr": GdsPnr, "bookingSourceOptions": [BookingSourceOption], "hotelShop": [HotelShop], "customText": [CustomText], "carSearch": CarSearch, "sharedCustomFields": [SharedCustomField], "tripOptions": TripOptions, "currencyCode": "abc123", "policyOptions": PolicyOptions, "airSearch": AirSearch, "sabreProfile": SabreProfile, "airportHubs": [AirportHub], "t2OptIn": T2OptIn, "configOptions": ConfigurationOptions, "railConnector": RailConnector, "hasFutureHotelSeasonalRates": false, "ruleClass": RuleClass, "ruleClasses": [RuleClass], "egenciaIntegration": 987, "contractExternalReferenceId": "xyz789" } } }` 

## Queries 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

139/246 

4/6/26, 2:27 PM 

config-api reference 

## **travelConfigByUuid** 

Looks up a travel config by UUID JWT Roles: companyadmin, travelsysadmin, sysadmin, travelagent, travelagentadmin, or travelagentnonbillable 

Response 

Returns a `TravelConfig` 

Arguments 

|Arguments||
|---|---|
|Name|Description|
|`uuid`-`String!`|v4 (preferred) or v5 uuid|



## **QUERY** 

```
query TravelConfigByUuid($uuid: String!){
travelConfigByUuid(uuid: $uuid){
id
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
fileId
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

140/246 

4/6/26, 2:27 PM 

config-api reference 

```
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
uuid
agencyName
agencyNumber
finisherProblemContact
address
companyId
daytimePhone
isActive
gdsType
gdsTypeName
nightPhone
pcc
profilePcc
ticketingPcc
ticketingTimeDeadline
vendorId
vendorName
wsAccessPoint
logo
daytimeHourStart
daytimeHourEnd
daytimeMessage
nightHourStart
nightHourEnd
nightMessage
virtualPaymentEnabled
fax
timeZone
agentId
sabreCreateContentCSLIUR
altAgentPcc
altAgentId
altAgentPassword
gdsPassword
altGdsPassword
agencyQueueConfigs {
...AgencyQueueConfigFragment
      }
agencyCancelPassiveSetting
agencyCancelTicketedSetting
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

141/246 

4/6/26, 2:27 PM 

config-api reference 

```
inMaintenanceMode
    }
company {
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
...MigrationFragment
      }
directBillContractReferenceId
customFields {
...CustomFieldFragment
      }
customText {
...CustomTextFragment
      }
domains {
...DomainFragment
      }
publishedFiles {
...PublishedFileFragment
      }
locations {
...LocationFragment
      }
modules {
...ModuleFragment
      }
orgUnits {
...OrgUnitFragment
      }
ruleClasses {
...RuleClassFragment
      }
travelConfigs {
...TravelConfigFragment
      }
companyGroups {
...CompanyGroupFragment
      }
t2OptIn {
...T2OptInFragment
      }
partnerServiceVendors {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

142/246 

4/6/26, 2:27 PM 

config-api reference 

```
...PartnerServiceVendorFragment
```

```
      }
    }
configurationItems {
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
configurationItemsHistory {
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
consortiumHotels {
discountCode
refName
    }
contractHotels {
chainCode
cdNumber
contractData
propertyId
contractRate
hotelRefName
hotelPrefRank
notes
currencyCode
countryCode
propertyInfo {
...PropertyInfoFragment
      }
seasonalRates {
...ContractHotelSeasonalRatesFragment
      }
    }
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

143/246 

4/6/26, 2:27 PM 

config-api reference 

```
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
eReceipt {
enableEreceipts
allowCliqbookItineraryForAirEreceipt
    }
emailOptions {
confirmationEmails
cancellationEmailSetting
holdReminderEmailSubject
approvalEmailOptions
    }
formOfPayment {
creditCardForAirRailRequired
govOnlyAirfareGhostCardNumber
govOnlyAirfareGhostCardType
govOnlyAirfareGhostCardExpiration
userCustomPropertyForDefaultCreditCard
enforceTempCardBinRestrictions
tempCardsHotelOnly
forceCreditCardChoice
showPersonalCardsBeforeGhostCards
    }
hotelSearch {
hotelMaxResults
preferredPropSearchRadius
companyLocationsSearchRadius
defaultHotelSearchRadius
hotelsWithDepositPermission
hotelDisplaysPerDiemRate
overrideBookingIataHotel
hotelSortDefault
hotelRateSortDefault
customHotelSortPrimary
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

144/246 

4/6/26, 2:27 PM 

config-api reference 

```
customHotelSortSecondary
customHotelSortTertiary
    }
pnrFinishing {
forceFinishingBeforeApproval
ticketOption
finishingTemplate {
...PublishedFileFragment
      }
addAllBrokenRulesToFinisher
    }
profileOptions {
requirePassportInfo
    }
wizardOptions {
showGovHotel
allowAddAirFfToCarHotel
cteTravelRequest
cteTravelRequestType
cteBookingSwitch
allowAddAirToExistingItin
serviceClassDefaultLowest
llfWindowSource
captureLlfFlifo
llfScreenShowWhen
llfScreenShowFlights
enableChurnDetection
churnAirlines
enableDuplicateDetection
dupDetectionAirlines
showMorningAfternoonEveningOptions
limitFarelistLlfWindow
showCommentsToAgentBox
showAgentCommentsWarning
maxCompanions
defaultDepartureHour
defaultReturnHour
mixedCarriersSplitMode
segmentFeesEnabled
fastTrackEnabled
    }
domains {
domainCode
name
nameMsgId
categories {
...TravelConfigCategoryFragment
      }
    }
travelConfigItems {
domainCode
categoryCode
itemCode
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

145/246 

4/6/26, 2:27 PM 

config-api reference 

```
defaultItemValue
enabled
mustBeEncrypted
travelConfigUuid
itemValue
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
tsaSecureFlight {
enforceSecureFlight
sendTsaData
allowBookingWithoutDob
writeMiddleNameToPnr
    }
profileSyncOptions {
xmlSyncIdDefault
gdsProfiles
gdsReadProfiles
syncBeforeSearch
    }
vendorDiscounts {
chainCode
isPreferred
extraData
prefRank
discountCode
travelCompanyType
airDiscountType
isCorporateRateOnlySearch
discountLevel
payAsYouFlyCode
promoCode
airMoreFaresBics
isRail
discountFlags {
...DiscountFlagsFragment
      }
    }
vendorExclusions {
chainCode
    }
violationReasons {
id
companyReasonCode
violationType
description
isActive
violationReasonCodeUUID
    }
gdsPnr {
writeUserSuppliedHotelPassives
requiresGdsPassive
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

146/246 

4/6/26, 2:27 PM 

config-api reference 

```
requiresGdsPnr
iWillBookLaterUserSuppliedOption
    }
bookingSourceOptions {
bookingSourceName
requiresGdsPassive
displayName
    }
hotelShop {
countryCode
shopGds
shopHotelService
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
customText {
fieldName
languageCode
value
useDefault
    }
carSearch {
carDeliveryCollectionLocationRadius
carDeliveryCollectionChains
alwaysRunCarGenShopRequest
carHomeDeliveryCollectionChains
overrideBookingIataCar
defaultCarType
carShopWithLoyaltyChains {
...CarLoyaltyVendorFragment
      }
    }
sharedCustomFields {
sharingId
attributeId
travelConfigId
nonGdsBookingSourceCode
partnerServiceVendorId
sharedAttributeId
companyId
sharedAttributeName
    }
tripOptions {
allowTripHold
maxHoldDays
maxDaysPassiveApprovalHold
autoCancelRejectedTrip
autoCancelRejectedNonAirTrip
autoCancelTripHold
autoCancelApprovalHold
allowTicketVoid
    }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

147/246 

4/6/26, 2:27 PM 

config-api reference 

```
currencyCode
policyOptions {
ruleClassLabel
userCanSelectRuleClass
rulesUseBaseFare
forceRuleClassSelection
allowMultipleViolationCodes
    }
airSearch {
showFlyAmericaCompliance
allowPreticketAirChange
allowPostticketAirChange
flexFaring
defaultAirSearchTimeWindowDomestic
defaultAirSearchTimeWindowInternational
llfTimeWindowDomestic
llfTimeWindowInternational
minAirSearchTimeWindow
maxAirSearchTimeWindow
defaultFlexFaringToMixedClass
useDomesticAirSearchTimeWindowForIntraregional
airSortDefault
scheduleSortDefault
customAirSortPrimary
customAirSortSecondary
customAirSortTertiary
customScheduleSortPrimary
customScheduleSortSecondary
customScheduleSortTertiary
ghostCardType
airLanes {
...AirLaneFragment
      }
airConnectors {
...AirConnectorFragment
      }
hideMultisegAirOption
maxPremiumShopResults
shopAcrossPaxTypes
airGuaranteedTicketingPermissions
masterPricerOptions
alternateFareOptions {
...AlternateFareOptionsFragment
      }
mobileAirBookingEnabled
simultaneousAirContracts
    }
sabreProfile {
sabreProfileDomainId
sabreProfileTemplateId
    }
airportHubs {
hubCode
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

148/246 

4/6/26, 2:27 PM 

config-api reference 

```
regionCityName
displayName
airportRegionId
airportCodes
airportCodesWithProperties {
...AirportHubPropertyFragment
      }
latitude
longitude
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
configOptions {
leaveUnusedFQVLNumbers
    }
railConnector {
evolviEnabled
sncfEnabled
amtrakEnabled
bibeEnabled
deutscheBahnEnabled
generalEnabled
renfeEnabled
searchParamsEnabled
silverRailEnabled
trainLineEnabled
viaRailEnabled
    }
hasFutureHotelSeasonalRates
ruleClass {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

149/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
egenciaIntegration
contractExternalReferenceId
  }
}
```

## **VARIABLES** 

```
{"uuid": "abc123"}
```

## **RESPONSE** 

```
{
"data": {
"travelConfigByUuid": {
"id": "abc123",
"uuid": "abc123",
"t2Id": "xyz789",
"outtaskId": "xyz789",
"travelConfigName": "xyz789",
"bar": "xyz789",
"profileTemplateFile": PublishedFile,
"isActive": false,
"castleEnabled": true,
"hasParent": true,
"gdsType": 987,
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

150/246 

4/6/26, 2:27 PM 

config-api reference 

```
"countryCode": "abc123",
"accountingCode": "xyz789",
"allowAddAirFfToCarHotel": false,
"allowPersonalCreditCardForHotel": false,
"allowTempCardForGuestBooking": true,
"requireCardForCarRental": false,
"agencyInvoiceFopChoice": 987,
"dontWritePassives": true,
"cteTravelRequest": false,
"cteTravelRequestType": 123,
"defaultPassiveSegments": true,
"itinMessage": "abc123",
"offlineTripPassiveApproval": false,
"usesLegacyHotelConnector": true,
"airPlusAidaEnabled": false,
"travelToolsUrl": "xyz789",
"brandingId": 123,
"agencyConfig": AgencyConfig,
"company": Company,
"configurationItems": [ConfigurationItem],
"configurationItemsHistory": [ConfigurationItem],
"consortiumHotels": [ConsortiumHotel],
"contractHotels": [ContractHotel],
"customFields": [CustomField],
"eReceipt": EReceipt,
"emailOptions": EmailOptions,
"formOfPayment": FormOfPayment,
"hotelSearch": HotelSearch,
"pnrFinishing": PnrFinishing,
"profileOptions": ProfileOptions,
"wizardOptions": WizardOptions,
"domains": [TravelConfigDomain],
"travelConfigItems": [TravelConfigItem],
"tsaSecureFlight": TsaSecureFlight,
"profileSyncOptions": ProfileSyncOptions,
"vendorDiscounts": [VendorDiscount],
"vendorExclusions": [VendorExclusion],
"violationReasons": [ViolationReason],
"gdsPnr": GdsPnr,
"bookingSourceOptions": [BookingSourceOption],
"hotelShop": [HotelShop],
"customText": [CustomText],
"carSearch": CarSearch,
"sharedCustomFields": [SharedCustomField],
"tripOptions": TripOptions,
"currencyCode": "xyz789",
"policyOptions": PolicyOptions,
"airSearch": AirSearch,
"sabreProfile": SabreProfile,
"airportHubs": [AirportHub],
"t2OptIn": T2OptIn,
"configOptions": ConfigurationOptions,
"railConnector": RailConnector,
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

151/246 

4/6/26, 2:27 PM 

config-api reference 

```
"hasFutureHotelSeasonalRates": false,
"ruleClass": RuleClass,
"ruleClasses": [RuleClass],
"egenciaIntegration": 987,
"contractExternalReferenceId": "abc123"
    }
  }
}
```

Queries 

## **travelConfigs** 

**Deprecated** No longer supported 

Response 

Returns a `TravelConfig` 

Arguments 

Name Description 

`uuid` - `String` 

`id` - `String` 

`limit` - `Int` 

## **QUERY** 

```
query TravelConfigs(
$uuid: String,
$id: String,
$limit: Int
){
travelConfigs(
    uuid: $uuid,
    id: $id,
    limit: $limit
  ){
id
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

152/246 

4/6/26, 2:27 PM 

config-api reference 

```
uuid
t2Id
outtaskId
travelConfigName
bar
profileTemplateFile {
fileId
companyId
purpose
subtype
fileName
fileExt
contentType
publishedFileData {
...PublishedFileDataFragment
      }
    }
isActive
castleEnabled
hasParent
gdsType
countryCode
accountingCode
allowAddAirFfToCarHotel
allowPersonalCreditCardForHotel
allowTempCardForGuestBooking
requireCardForCarRental
agencyInvoiceFopChoice
dontWritePassives
cteTravelRequest
cteTravelRequestType
defaultPassiveSegments
itinMessage
offlineTripPassiveApproval
usesLegacyHotelConnector
airPlusAidaEnabled
travelToolsUrl
brandingId
agencyConfig {
uuid
agencyName
agencyNumber
finisherProblemContact
address
companyId
daytimePhone
isActive
gdsType
gdsTypeName
nightPhone
pcc
profilePcc
ticketingPcc
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

153/246 

4/6/26, 2:27 PM 

config-api reference 

```
ticketingTimeDeadline
vendorId
vendorName
wsAccessPoint
logo
daytimeHourStart
daytimeHourEnd
daytimeMessage
nightHourStart
nightHourEnd
nightMessage
virtualPaymentEnabled
fax
timeZone
agentId
sabreCreateContentCSLIUR
altAgentPcc
altAgentId
altAgentPassword
gdsPassword
altGdsPassword
agencyQueueConfigs {
...AgencyQueueConfigFragment
      }
agencyCancelPassiveSetting
agencyCancelTicketedSetting
inMaintenanceMode
    }
company {
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
...MigrationFragment
      }
directBillContractReferenceId
customFields {
...CustomFieldFragment
      }
customText {
...CustomTextFragment
      }
domains {
...DomainFragment
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

154/246 

4/6/26, 2:27 PM 

config-api reference 

```
      }
```

```
publishedFiles {
...PublishedFileFragment
      }
locations {
...LocationFragment
      }
modules {
...ModuleFragment
      }
orgUnits {
...OrgUnitFragment
      }
ruleClasses {
...RuleClassFragment
      }
travelConfigs {
...TravelConfigFragment
      }
companyGroups {
...CompanyGroupFragment
      }
t2OptIn {
...T2OptInFragment
      }
partnerServiceVendors {
...PartnerServiceVendorFragment
      }
    }
configurationItems {
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
configurationItemsHistory {
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
    }
consortiumHotels {
discountCode
refName
    }
contractHotels {
chainCode
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

155/246 

4/6/26, 2:27 PM 

config-api reference 

```
cdNumber
contractData
propertyId
contractRate
hotelRefName
hotelPrefRank
notes
currencyCode
countryCode
propertyInfo {
...PropertyInfoFragment
      }
seasonalRates {
...ContractHotelSeasonalRatesFragment
      }
    }
customFields {
uuid
id
attributeId
attributeType
name
dataType
required
minLength
maxLength
displayOnItinerary
displayTitle
displayAtStart
displayAtEnd
sort
totalValues
dependencyFieldId
dependencyFieldUuid
dependencyValues
dependencyType
displayForGuestBooking
displayForRegularTrips
displayForTripEdits
displayForMeetings
customFieldValues {
...CustomFieldValueFragment
      }
dependsOnField {
...CustomFieldFragment
      }
    }
eReceipt {
enableEreceipts
allowCliqbookItineraryForAirEreceipt
    }
emailOptions {
confirmationEmails
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

156/246 

4/6/26, 2:27 PM 

config-api reference 

```
cancellationEmailSetting
holdReminderEmailSubject
approvalEmailOptions
    }
formOfPayment {
creditCardForAirRailRequired
govOnlyAirfareGhostCardNumber
govOnlyAirfareGhostCardType
govOnlyAirfareGhostCardExpiration
userCustomPropertyForDefaultCreditCard
enforceTempCardBinRestrictions
tempCardsHotelOnly
forceCreditCardChoice
showPersonalCardsBeforeGhostCards
    }
hotelSearch {
hotelMaxResults
preferredPropSearchRadius
companyLocationsSearchRadius
defaultHotelSearchRadius
hotelsWithDepositPermission
hotelDisplaysPerDiemRate
overrideBookingIataHotel
hotelSortDefault
hotelRateSortDefault
customHotelSortPrimary
customHotelSortSecondary
customHotelSortTertiary
    }
pnrFinishing {
forceFinishingBeforeApproval
ticketOption
finishingTemplate {
...PublishedFileFragment
      }
addAllBrokenRulesToFinisher
    }
profileOptions {
requirePassportInfo
    }
wizardOptions {
showGovHotel
allowAddAirFfToCarHotel
cteTravelRequest
cteTravelRequestType
cteBookingSwitch
allowAddAirToExistingItin
serviceClassDefaultLowest
llfWindowSource
captureLlfFlifo
llfScreenShowWhen
llfScreenShowFlights
enableChurnDetection
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

157/246 

4/6/26, 2:27 PM 

config-api reference 

```
churnAirlines
enableDuplicateDetection
dupDetectionAirlines
showMorningAfternoonEveningOptions
limitFarelistLlfWindow
showCommentsToAgentBox
showAgentCommentsWarning
maxCompanions
defaultDepartureHour
defaultReturnHour
mixedCarriersSplitMode
segmentFeesEnabled
fastTrackEnabled
    }
domains {
domainCode
name
nameMsgId
categories {
...TravelConfigCategoryFragment
      }
    }
travelConfigItems {
domainCode
categoryCode
itemCode
defaultItemValue
enabled
mustBeEncrypted
travelConfigUuid
itemValue
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
tsaSecureFlight {
enforceSecureFlight
sendTsaData
allowBookingWithoutDob
writeMiddleNameToPnr
    }
profileSyncOptions {
xmlSyncIdDefault
gdsProfiles
gdsReadProfiles
syncBeforeSearch
    }
vendorDiscounts {
chainCode
isPreferred
extraData
prefRank
discountCode
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

158/246 

4/6/26, 2:27 PM 

config-api reference 

```
travelCompanyType
airDiscountType
isCorporateRateOnlySearch
discountLevel
payAsYouFlyCode
promoCode
airMoreFaresBics
isRail
discountFlags {
...DiscountFlagsFragment
      }
    }
vendorExclusions {
chainCode
    }
violationReasons {
id
companyReasonCode
violationType
description
isActive
violationReasonCodeUUID
    }
gdsPnr {
writeUserSuppliedHotelPassives
requiresGdsPassive
requiresGdsPnr
iWillBookLaterUserSuppliedOption
    }
bookingSourceOptions {
bookingSourceName
requiresGdsPassive
displayName
    }
hotelShop {
countryCode
shopGds
shopHotelService
partnerServiceVendor {
...PartnerServiceVendorFragment
      }
    }
customText {
fieldName
languageCode
value
useDefault
    }
carSearch {
carDeliveryCollectionLocationRadius
carDeliveryCollectionChains
alwaysRunCarGenShopRequest
carHomeDeliveryCollectionChains
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

159/246 

4/6/26, 2:27 PM 

config-api reference 

```
overrideBookingIataCar
defaultCarType
carShopWithLoyaltyChains {
...CarLoyaltyVendorFragment
      }
    }
sharedCustomFields {
sharingId
attributeId
travelConfigId
nonGdsBookingSourceCode
partnerServiceVendorId
sharedAttributeId
companyId
sharedAttributeName
    }
tripOptions {
allowTripHold
maxHoldDays
maxDaysPassiveApprovalHold
autoCancelRejectedTrip
autoCancelRejectedNonAirTrip
autoCancelTripHold
autoCancelApprovalHold
allowTicketVoid
    }
currencyCode
policyOptions {
ruleClassLabel
userCanSelectRuleClass
rulesUseBaseFare
forceRuleClassSelection
allowMultipleViolationCodes
    }
airSearch {
showFlyAmericaCompliance
allowPreticketAirChange
allowPostticketAirChange
flexFaring
defaultAirSearchTimeWindowDomestic
defaultAirSearchTimeWindowInternational
llfTimeWindowDomestic
llfTimeWindowInternational
minAirSearchTimeWindow
maxAirSearchTimeWindow
defaultFlexFaringToMixedClass
useDomesticAirSearchTimeWindowForIntraregional
airSortDefault
scheduleSortDefault
customAirSortPrimary
customAirSortSecondary
customAirSortTertiary
customScheduleSortPrimary
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

160/246 

4/6/26, 2:27 PM 

config-api reference 

```
customScheduleSortSecondary
customScheduleSortTertiary
ghostCardType
airLanes {
...AirLaneFragment
      }
airConnectors {
...AirConnectorFragment
      }
hideMultisegAirOption
maxPremiumShopResults
shopAcrossPaxTypes
airGuaranteedTicketingPermissions
masterPricerOptions
alternateFareOptions {
...AlternateFareOptionsFragment
      }
mobileAirBookingEnabled
simultaneousAirContracts
    }
sabreProfile {
sabreProfileDomainId
sabreProfileTemplateId
    }
airportHubs {
hubCode
regionCityName
displayName
airportRegionId
airportCodes
airportCodesWithProperties {
...AirportHubPropertyFragment
      }
latitude
longitude
    }
t2OptIn {
airOptIn
carOptIn
hotelOptIn
companyAirOptIn
companyCarOptIn
companyHotelOptIn
tmcAirOptIn
tmcCarOptIn
tmcHotelOptIn
uuids
adminOnly
    }
configOptions {
leaveUnusedFQVLNumbers
    }
railConnector {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

161/246 

4/6/26, 2:27 PM 

config-api reference 

```
evolviEnabled
sncfEnabled
amtrakEnabled
bibeEnabled
deutscheBahnEnabled
generalEnabled
renfeEnabled
searchParamsEnabled
silverRailEnabled
trainLineEnabled
viaRailEnabled
    }
hasFutureHotelSeasonalRates
ruleClass {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
ruleClasses {
id
ruleClassId
ruleClassUuid
ruleClassName
propertyConfigId
allowLimo
enableUserSuppliedHotels
approval {
...ApprovalFragment
      }
customFields {
...CustomFieldFragment
      }
ruleValues {
...RuleValueFragment
      }
itineraryRulesCustomFieldCount
    }
egenciaIntegration
contractExternalReferenceId
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

162/246 

4/6/26, 2:27 PM 

config-api reference 

```
  }
}
```

## **VARIABLES** 

```
{
"uuid": "xyz789",
"id": "abc123",
"limit": 987
}
```

## **RESPONSE** 

```
{
"data": {
"travelConfigs": {
"id": "xyz789",
"uuid": "xyz789",
"t2Id": "abc123",
"outtaskId": "abc123",
"travelConfigName": "abc123",
"bar": "abc123",
"profileTemplateFile": PublishedFile,
"isActive": false,
"castleEnabled": true,
"hasParent": true,
"gdsType": 123,
"countryCode": "xyz789",
"accountingCode": "abc123",
"allowAddAirFfToCarHotel": false,
"allowPersonalCreditCardForHotel": true,
"allowTempCardForGuestBooking": true,
"requireCardForCarRental": false,
"agencyInvoiceFopChoice": 987,
"dontWritePassives": true,
"cteTravelRequest": true,
"cteTravelRequestType": 987,
"defaultPassiveSegments": true,
"itinMessage": "abc123",
"offlineTripPassiveApproval": false,
"usesLegacyHotelConnector": false,
"airPlusAidaEnabled": false,
"travelToolsUrl": "xyz789",
"brandingId": 987,
"agencyConfig": AgencyConfig,
"company": Company,
"configurationItems": [ConfigurationItem],
"configurationItemsHistory": [ConfigurationItem],
"consortiumHotels": [ConsortiumHotel],
"contractHotels": [ContractHotel],
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

163/246 

4/6/26, 2:27 PM 

config-api reference 

```
"customFields": [CustomField],
"eReceipt": EReceipt,
"emailOptions": EmailOptions,
"formOfPayment": FormOfPayment,
"hotelSearch": HotelSearch,
"pnrFinishing": PnrFinishing,
"profileOptions": ProfileOptions,
"wizardOptions": WizardOptions,
"domains": [TravelConfigDomain],
"travelConfigItems": [TravelConfigItem],
"tsaSecureFlight": TsaSecureFlight,
"profileSyncOptions": ProfileSyncOptions,
"vendorDiscounts": [VendorDiscount],
"vendorExclusions": [VendorExclusion],
"violationReasons": [ViolationReason],
"gdsPnr": GdsPnr,
"bookingSourceOptions": [BookingSourceOption],
"hotelShop": [HotelShop],
"customText": [CustomText],
"carSearch": CarSearch,
"sharedCustomFields": [SharedCustomField],
"tripOptions": TripOptions,
"currencyCode": "abc123",
"policyOptions": PolicyOptions,
"airSearch": AirSearch,
"sabreProfile": SabreProfile,
"airportHubs": [AirportHub],
"t2OptIn": T2OptIn,
"configOptions": ConfigurationOptions,
"railConnector": RailConnector,
"hasFutureHotelSeasonalRates": false,
"ruleClass": RuleClass,
"ruleClasses": [RuleClass],
"egenciaIntegration": 123,
"contractExternalReferenceId": "abc123"
    }
  }
}
```

Queries 

## **travelConfigsByCompanyAndAgency** 

Response 

Returns `[TravelConfigTuple!]!` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

164/246 

4/6/26, 2:27 PM 

config-api reference 

Arguments 

## Name 

## Description 

`companyUuid` - `String!` 

## `agencyCompanyUuid` - `String!` 

## **QUERY** 

```
query TravelConfigsByCompanyAndAgency(
$companyUuid: String!,
$agencyCompanyUuid: String!
){
travelConfigsByCompanyAndAgency(
    companyUuid: $companyUuid,
    agencyCompanyUuid: $agencyCompanyUuid
  ){
uuid
travelConfigName
  }
}
```

## **VARIABLES** 

```
{
"companyUuid": "xyz789",
"agencyCompanyUuid": "xyz789"
}
```

## **RESPONSE** 

```
{
"data": {
"travelConfigsByCompanyAndAgency": [
      {
"uuid": "xyz789",
"travelConfigName": "xyz789"
      }
    ]
  }
}
```

## Queries 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

165/246 

4/6/26, 2:27 PM 

config-api reference 

## **userByUuid** 

Looks up user info given user uuid 

Response 

Returns a `User` 

Arguments 

Name Description 

`uuid` - `String!` 

## **QUERY** 

```
query UserByUuid($uuid: String!){
userByUuid(uuid: $uuid){
id
company {
id
companyId
companyName
internetDomain
companyDomain
countryCode
billingCurrencyCode
uuid
activeSwitch
isBillable
travelOfferingCode
isUatCompany
migration {
...MigrationFragment
      }
directBillContractReferenceId
customFields {
...CustomFieldFragment
      }
customText {
...CustomTextFragment
      }
domains {
...DomainFragment
      }
publishedFiles {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

166/246 

4/6/26, 2:27 PM 

config-api reference 

```
...PublishedFileFragment
      }
locations {
...LocationFragment
      }
modules {
...ModuleFragment
      }
orgUnits {
...OrgUnitFragment
      }
ruleClasses {
...RuleClassFragment
      }
travelConfigs {
...TravelConfigFragment
      }
companyGroups {
...CompanyGroupFragment
      }
t2OptIn {
...T2OptInFragment
      }
partnerServiceVendors {
...PartnerServiceVendorFragment
      }
    }
meetings {
outtaskId
name
locationName
cityCodes
startDate
endDate
matchingStartDate
matchingEndDate
timeZone
    }
companiesAccess {
uuid
companyName
    }
travelConfigsAccess {
uuid
travelConfigName
    }
canAccessCompany
canAccessTravelConfig
  }
}
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

167/246 

4/6/26, 2:27 PM 

config-api reference 

## **VARIABLES** 

```
{"uuid": "abc123"}
```

## **RESPONSE** 

```
{
"data": {
"userByUuid": {
"id": "abc123",
"company": Company,
"meetings": [Meeting],
"companiesAccess": [CompanyTuple],
"travelConfigsAccess": [TravelConfigTuple],
"canAccessCompany": true,
"canAccessTravelConfig": false
    }
  }
}
```

Queries 

## **vendorDiscountsByUser** 

Returns vendor discounts at org unit-level, travel config-level, and company-wide-level for the given user. If there are multiple discounts for the same vendor, any discounts at the org unitlevel override any travel config-level discounts, and travel config-level discounts override company-wide-level discounts. 

Response 

Returns `[VendorDiscount]` 

Arguments 

|Arguments||
|---|---|
|Name|Description|
|`uuid`-`String!`|A users UUID|



https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

168/246 

4/6/26, 2:27 PM 

config-api reference 

Description 

Name 

If travelConfigUuid is provided, it will override `travelConfigUuid` - `String` the travel config and gdsType associated with the user in the discount results. If travelType is provided, will only return `travelType` - `String` 

If travelType is provided, will only return discounts of the specified type (A, C, H). Default is true, if set to false all discounts are returned for all levels 

`applyFilter` - `Boolean` 

## **QUERY** 

```
query VendorDiscountsByUser(
$uuid: String!,
$travelConfigUuid: String,
$travelType: String,
$applyFilter: Boolean
){
vendorDiscountsByUser(
    uuid: $uuid,
    travelConfigUuid: $travelConfigUuid,
    travelType: $travelType,
    applyFilter: $applyFilter
  ){
chainCode
isPreferred
extraData
prefRank
discountCode
travelCompanyType
airDiscountType
isCorporateRateOnlySearch
discountLevel
payAsYouFlyCode
promoCode
airMoreFaresBics
isRail
discountFlags {
sabreKeepUndiscountedCars
airPrivateDiscountFaresOnly
airPrivateAndPublicSeparateSearch
amadeusCorporateSeparateSearch
    }
  }
}
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

169/246 

4/6/26, 2:27 PM 

config-api reference 

## **VARIABLES** 

```
{
"uuid": "abc123",
"travelConfigUuid": "abc123",
"travelType": "xyz789",
"applyFilter": true
}
```

## **RESPONSE** 

```
{
"data": {
"vendorDiscountsByUser": [
      {
"chainCode": "abc123",
"isPreferred": true,
"extraData": "xyz789",
"prefRank": 987,
"discountCode": "abc123",
"travelCompanyType": "abc123",
"airDiscountType": "abc123",
"isCorporateRateOnlySearch": true,
"discountLevel": "abc123",
"payAsYouFlyCode": "xyz789",
"promoCode": "abc123",
"airMoreFaresBics": "abc123",
"isRail": true,
"discountFlags": DiscountFlags
      }
    ]
  }
}
```

Mutations 

## **createConfigurationItem** 

Response 

Returns a `ConfigurationItem` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

170/246 

4/6/26, 2:27 PM 

config-api reference 

Arguments 

## Name 

Description 

`input` - `ConfigurationItemInput!` 

## **QUERY** 

```
mutation CreateConfigurationItem($input: ConfigurationItemInput!){
createConfigurationItem(input: $input){
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
  }
}
```

## **VARIABLES** 

```
{"input": ConfigurationItemInput}
```

## **RESPONSE** 

```
{
"data": {
"createConfigurationItem": {
"domain": "xyz789",
"category": "abc123",
"item": "xyz789",
"value": "xyz789",
"lastModifiedBy": "abc123",
"lastModifiedUtc": "xyz789",
"companyUuid": "xyz789"
    }
  }
}
```

## Mutations 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

171/246 

4/6/26, 2:27 PM 

config-api reference 

## **deleteConfigurationItem** 

Response 

Returns a `ConfigurationItem` 

Arguments 

Name Description 

`input` - `ConfigurationItemInput!` 

## **QUERY** 

```
mutation DeleteConfigurationItem($input: ConfigurationItemInput!){
deleteConfigurationItem(input: $input){
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
  }
}
```

## **VARIABLES** 

```
{"input": ConfigurationItemInput}
```

## **RESPONSE** 

```
{
"data": {
"deleteConfigurationItem": {
"domain": "xyz789",
"category": "xyz789",
"item": "xyz789",
"value": "abc123",
"lastModifiedBy": "xyz789",
"lastModifiedUtc": "abc123",
"companyUuid": "abc123"
    }
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

172/246 

4/6/26, 2:27 PM 

config-api reference 

```
}
```

Mutations 

## **updateConfigurationItem** 

Response 

Returns a `ConfigurationItem` 

Arguments 

Name Description 

`input` - `ConfigurationItemInput!` 

## **QUERY** 

```
mutation UpdateConfigurationItem($input: ConfigurationItemInput!){
updateConfigurationItem(input: $input){
domain
category
item
value
lastModifiedBy
lastModifiedUtc
companyUuid
  }
}
```

## **VARIABLES** 

```
{"input": ConfigurationItemInput}
```

## **RESPONSE** 

```
{
"data": {
"updateConfigurationItem": {
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

173/246 

4/6/26, 2:27 PM 

config-api reference 

```
"domain": "abc123",
"category": "xyz789",
"item": "abc123",
"value": "xyz789",
"lastModifiedBy": "xyz789",
"lastModifiedUtc": "xyz789",
"companyUuid": "xyz789"
    }
  }
}
```

Types 

## **AgencyConfig** 

Field Name Description 

`uuid` - `String` 

`agencyName` - `String` 

`agencyNumber` - `String` 

`finisherProblemContact` - `String` 

`address` - `String` 

`companyId` - `Int` 

`daytimePhone` - `String` 

`isActive` - `Boolean` 

`gdsType` - `Int` 

`gdsTypeName` - `String!` 

`nightPhone` - `String` 

`pcc` - `String` 

`profilePcc` - `String` 

`ticketingPcc` - `String` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

174/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`ticketingTimeDeadline` - `String` 

`vendorId` - `Int` 

`vendorName` - `String` 

`wsAccessPoint` - `String` 

`logo` - `String` 

`daytimeHourStart` - `String` 

`daytimeHourEnd` - `String` 

`daytimeMessage` - `String` 

`nightHourStart` - `String` 

`nightHourEnd` - `String` 

`nightMessage` - `String` 

`virtualPaymentEnabled` - `Boolean!` 

**Deprecated** This field is not updated anymore. Use vpay service instead. 

`fax` - `String` 

`timeZone` - `String` The time zone identifier (aka Olson Name) 

`agentId` - `String` 

`sabreCreateContentCSLIUR` - `Boolean` 

If sabreCreateContentCSLIUR = true, this means checkbox Create Content Services for Lodging (CSL) Interface User Record (IUR) is checked 

`altAgentPcc` - `String` 

`altAgentId` - `String` 

`altAgentPassword` - `String` 

`gdsPassword` - `String` 

`altGdsPassword` - `String` 

`agencyQueueConfigs` - `[AgencyQueueConfig]` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

175/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`agencyCancelPassiveSetting` - `Int` 

`agencyCancelTicketedSetting` - `Int` 

`inMaintenanceMode` - `Boolean` 

Possible values: 0 = Not allowed, 1 = Send to queue, 2 = Cancel live segments 

Possible values: 0 = Not allowed, 1 = Send to queue, 2 = Cancel live segments 

If InMaintenanceMode is true, this means the Sabre Agent Account is blocked 

## **EXAMPLE** 

```
{
"uuid": "xyz789",
"agencyName": "xyz789",
"agencyNumber": "xyz789",
"finisherProblemContact": "abc123",
"address": "abc123",
"companyId": 123,
"daytimePhone": "xyz789",
"isActive": false,
"gdsType": 987,
"gdsTypeName": "xyz789",
"nightPhone": "xyz789",
"pcc": "abc123",
"profilePcc": "xyz789",
"ticketingPcc": "abc123",
"ticketingTimeDeadline": "abc123",
"vendorId": 123,
"vendorName": "xyz789",
"wsAccessPoint": "xyz789",
"logo": "abc123",
"daytimeHourStart": "xyz789",
"daytimeHourEnd": "xyz789",
"daytimeMessage": "xyz789",
"nightHourStart": "xyz789",
"nightHourEnd": "abc123",
"nightMessage": "xyz789",
"virtualPaymentEnabled": false,
"fax": "xyz789",
"timeZone": "abc123",
"agentId": "xyz789",
"sabreCreateContentCSLIUR": true,
"altAgentPcc": "xyz789",
"altAgentId": "xyz789",
"altAgentPassword": "abc123",
"gdsPassword": "abc123",
"altGdsPassword": "xyz789",
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

176/246 

4/6/26, 2:27 PM 

config-api reference 

```
"agencyQueueConfigs": [AgencyQueueConfig],
"agencyCancelPassiveSetting": 987,
"agencyCancelTicketedSetting": 987,
"inMaintenanceMode": true
}
```

Types 

## **AgencyQueue** 

Field Name 

Description 

`lastModBy` - `Int` 

`optionalInfo` - `String` 

`priority` - `Int` 

`pseudoCity` - `String` 

`queueConfigId` - `Int` 

`queueModifier` - `String` 

`queueNumber` - `Int` 

`queueType` - `String` 

## **EXAMPLE** 

```
{
"lastModBy": 987,
"optionalInfo": "abc123",
"priority": 987,
"pseudoCity": "xyz789",
"queueConfigId": 123,
"queueModifier": "xyz789",
"queueNumber": 987,
"queueType": "abc123"
}
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

177/246 

4/6/26, 2:27 PM 

config-api reference 

Types 

## **AgencyQueueConfig** 

Field Name Description `agencyId` - `Int agencyQueues` - `[AgencyQueue] configName` - `String queueConfigId` - `Int` 

**EXAMPLE** `{ "agencyId": 123, "agencyQueues": [AgencyQueue], "configName": "abc123", "queueConfigId": 123 }` 

## Types 

## **AirConnector** 

Field Name Description `name` - `String default` - `Boolean includes` - `[String] excludes` - `[String]` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

178/246 

4/6/26, 2:27 PM 

config-api reference 

## **EXAMPLE** 

```
{
"name": "abc123",
"default": true,
"includes": ["xyz789"],
"excludes": ["xyz789"]
}
```

Types 

## **AirLane** 

Field Name Description `city1` - `String city2` - `String` 

`almostPreferredPriceDifference` - `Float travelerMessage` - `String` 

`preferredVendorPriceDifference` - `Float` 

`startDate` - `DateTime` 

`endDate` - `DateTime` 

`airLaneCarriers` - `[AirLaneCarrier]` 

## **EXAMPLE** 

```
{
"city1": "abc123",
"city2": "abc123",
"almostPreferredPriceDifference": 987.65,
"travelerMessage": "xyz789",
"preferredVendorPriceDifference": 987.65,
"startDate": "2007-12-03T10:15:30Z",
"endDate": "2007-12-03T10:15:30Z",
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

179/246 

4/6/26, 2:27 PM 

config-api reference 

```
"airLaneCarriers": [AirLaneCarrier]
```

```
}
```

Types 

## **AirLaneCarrier** 

Field Name 

Description 

`airline` - `String` 

`carrierType` - `Int` 

`prefRank` - `Int` 

`hideAgencyPreferredIcon` - `Boolean` 

`hidePreferenceLevelIcon` - `Boolean` 

## **EXAMPLE** 

```
{
"airline": "abc123",
"carrierType": 987,
"prefRank": 123,
"hideAgencyPreferredIcon": true,
"hidePreferenceLevelIcon": false
}
```

Types 

## **AirSearch** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

180/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`showFlyAmericaCompliance` - `Boolean` 

`allowPreticketAirChange` - `Int` 

`allowPostticketAirChange` - `Int` 

`flexFaring` - `Int` 

`defaultAirSearchTimeWindowDomestic` - `Int!` Possible values: Int between 1-8 

`defaultAirSearchTimeWindowInternational` - 

Possible values: Int between 1-8 

```
Int!
```

`llfTimeWindowDomestic` - `Int` Possible values: Int between 1-8 `llfTimeWindowInternational` - `Int` Possible values: Int between 1-8 

`minAirSearchTimeWindow` - `Int!` 

`maxAirSearchTimeWindow` - `Int` 

`defaultFlexFaringToMixedClass` - `Boolean` 

```
useDomesticAirSearchTimeWindowForIntraregional
```

- `Boolean!` 

`airSortDefault` - `String!` 

`scheduleSortDefault` - `String` 

`customAirSortPrimary` - `String` 

`customAirSortSecondary` - `String` 

`customAirSortTertiary` - `String` 

`customScheduleSortPrimary` - `String` 

`customScheduleSortSecondary` - `String` 

`customScheduleSortTertiary` - `String` 

`ghostCardType` - `String` 

if ghostCardType = "##" then Use agency invoice for GDS Air is selected 

`airLanes` - `[AirLane]` 

`airConnectors` - `[AirConnector]` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

181/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name Description 

`hideMultisegAirOption` - `Boolean! maxPremiumShopResults` - `Int shopAcrossPaxTypes` - `Boolean` Access to Guaranteed Ticketing carriers: 

0 = Guaranteed Ticketing carriers not available 1 = Allow if fare violates no rules `airGuaranteedTicketingPermissions` - `Int!` 2 = Allow unless manager approval is required 3 = Show but don't allow 4 = Allow masterPricerOptions for Amadeus GDS type only: 2 = Always `masterPricerOptions` - `Int` 4 = Travel 7 or more days out 8 = Travel 14 or more days out 16 = Travel 21 or more days out 32 = Never alternateFareOptions for Amadeus GDS type `alternateFareOptions` - `AlternateFareOptions` only `mobileAirBookingEnabled` - `Boolean! simultaneousAirContracts` - `Int` Possible values vary by GDS: Int between 1-10 

## **EXAMPLE** 

```
{
"showFlyAmericaCompliance": false,
"allowPreticketAirChange": 987,
"allowPostticketAirChange": 987,
"flexFaring": 987,
"defaultAirSearchTimeWindowDomestic": 987,
"defaultAirSearchTimeWindowInternational": 123,
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

182/246 

4/6/26, 2:27 PM 

config-api reference 

```
"llfTimeWindowDomestic": 123,
"llfTimeWindowInternational": 987,
"minAirSearchTimeWindow": 987,
"maxAirSearchTimeWindow": 987,
"defaultFlexFaringToMixedClass": true,
"useDomesticAirSearchTimeWindowForIntraregional": true,
"airSortDefault": "xyz789",
"scheduleSortDefault": "xyz789",
"customAirSortPrimary": "xyz789",
"customAirSortSecondary": "abc123",
"customAirSortTertiary": "abc123",
"customScheduleSortPrimary": "abc123",
"customScheduleSortSecondary": "xyz789",
"customScheduleSortTertiary": "abc123",
"ghostCardType": "abc123",
"airLanes": [AirLane],
"airConnectors": [AirConnector],
"hideMultisegAirOption": true,
"maxPremiumShopResults": 123,
"shopAcrossPaxTypes": false,
"airGuaranteedTicketingPermissions": 123,
"masterPricerOptions": 987,
"alternateFareOptions": AlternateFareOptions,
"mobileAirBookingEnabled": false,
"simultaneousAirContracts": 123
}
```

Types 

## **AirportHub** 

Field Name 

Description 

`hubCode` - `String` 

`regionCityName` - `String` 

`displayName` - `String` 

`airportRegionId` - `Int` 

`airportCodes` - `[String]` 

@deprecated Use airportCodesWithProperties for preference information **Deprecated** Use 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

183/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

airportCodesWithProperties for preference information 

## `airportCodesWithProperties` - 

```
[AirportHubProperty]
```

`latitude` - `Float` 

`longitude` - `Float` 

## **EXAMPLE** 

```
{
"hubCode": "xyz789",
"regionCityName": "xyz789",
"displayName": "abc123",
"airportRegionId": 123,
"airportCodes": ["xyz789"],
"airportCodesWithProperties": [AirportHubProperty],
"latitude": 987.65,
"longitude": 987.65
}
```

Types 

## **AirportHubProperty** 

Field Name Description `iataCode` - `String` 0 = General `propType` - `String` 1 = Airline `propValue` - `String` From UI: 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

184/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

**General** shops take a numeric value from 0 to 99 that is the relative preference of the airport compared to the others **Airline** specific shops take a 2-letter IATA airline code for the carrier to always look for at this airport. 

## **EXAMPLE** 

```
{
"iataCode": "abc123",
"propType": "abc123",
"propValue": "abc123"
}
```

Types 

## **AlternateFareOptions** 

Field Name Description 

`leastCostOnPlane` - `Boolean!` 

`leastCostInCabin` - `Boolean!` 

`unrestrictedInCabin` - `Boolean!` 

`unrestrictedInCoach` - `Boolean!` 

## **EXAMPLE** 

```
{
"leastCostOnPlane": false,
"leastCostInCabin": false,
"unrestrictedInCabin": true,
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

185/246 

4/6/26, 2:27 PM 

config-api reference 

```
"unrestrictedInCoach": true
```

```
}
```

Types 

## **Approval** 

**DEPRECATED** Represents approval settings for rule classes 

Field Name Description 

`managers` - `Int` 

`approvers` - `[String]` 

## **EXAMPLE** 

```
{"managers": 987, "approvers": ["xyz789"]}
```

Types 

## **AuthZ** 

Field Name Description 

`tripLinkAdmin` - `Boolean` 

`companySelect` - `Boolean` 

## **EXAMPLE** 

```
{"tripLinkAdmin": true, "companySelect": true}
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

186/246 

4/6/26, 2:27 PM 

config-api reference 

Types 

## **BigDecimal** 

## **EXAMPLE** 

```
BigDecimal
```

Types 

## **BookingSourceOption** 

Field Name Description `bookingSourceName` - `String` null = Use default `requiresGdsPassive` - `Boolean` true = Always write passives false = Never write passives `displayName` - `String` **EXAMPLE** `{ "bookingSourceName": "abc123", "requiresGdsPassive": true, "displayName": "xyz789" }` 

Types 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

187/246 

4/6/26, 2:27 PM 

config-api reference 

## **Boolean** 

The `Boolean` scalar type represents `true` or `false` . 

Types 

## **CarLoyaltyVendor** 

Field Name Description `vendor` - `String` 

## **EXAMPLE** 

```
{"vendor": "xyz789"}
```

Types 

## **CarSearch** 

Field Name Description `carDeliveryCollectionLocationRadius` - `Int carDeliveryCollectionChains` - `String alwaysRunCarGenShopRequest` - `Int carHomeDeliveryCollectionChains` - `String overrideBookingIataCar` - `String defaultCarType` - `String!` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

188/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`carShopWithLoyaltyChains` - 

```
[CarLoyaltyVendor]
```

## **EXAMPLE** 

```
{
"carDeliveryCollectionLocationRadius": 123,
"carDeliveryCollectionChains": "abc123",
"alwaysRunCarGenShopRequest": 987,
"carHomeDeliveryCollectionChains": "xyz789",
"overrideBookingIataCar": "abc123",
"defaultCarType": "abc123",
"carShopWithLoyaltyChains": [CarLoyaltyVendor]
}
```

Types 

## **Companies** 

Field Name Description 

`pageInfo` - `PageInfo!` 

`companies` - `[Company]` 

## **EXAMPLE** 

```
{
"pageInfo": PageInfo,
"companies": [Company]
}
```

Types 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

189/246 

4/6/26, 2:27 PM 

config-api reference 

## **Company** 

OUTTASK_COMPANY - represents a company 

|Field Name|Description||
|---|---|---|
|`id`-`String`|**Deprecated** This returns a v5 uuid which is not<br>valid for company. Use uuid field instead||
|`companyId`-`Int`|||
|`companyName`-`String`|**Deprecated**|Prefer profile v1/v4 for this data|
|`internetDomain`-`String`|**Deprecated**|Prefer profile v1/v4 for this data|
|`companyDomain`-`String`|**Deprecated**|Prefer profile v1/v4 for this data|
|`countryCode`-`String`|**Deprecated**|Prefer profile v1/v4 for this data|
|`billingCurrencyCode`-`String`|||
|`uuid`-`String`|||
|`activeSwitch`-`Int`|**Deprecated**|Prefer profile v1/v4 for this data|
|`isBillable`-`Boolean`|**Deprecated**|Prefer profile v1/v4 for this data|
|`travelOfferingCode`-`String`|**Deprecated**|Prefer profile v1/v4 for this data|
|`isUatCompany`-`Boolean`|**Deprecated**|Prefer profile v1/v4 for this data|
|`migration`-`Migration`|**Deprecated**|Prefer profile v1/v4 for this data|
|`directBillContractReferenceId`-`String`|||
|`customFields`-`[CustomField]`|||



Arguments 

`type` - `String` Possible values: 'trip' or 'user' 

`customText` - `[CustomText]` 

Arguments 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

190/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`fieldName` - `[String]` 

`languageCode` - `String` 

`showEmpty` - `Boolean` 

Default: false 

`domains` - `[Domain]` 

`publishedFiles` - `[PublishedFile]` 

`locations` - `[Location]` 

`modules` - `[Module]` 

Arguments 

`moduleCode` - `[String!]` 

`orgUnits` - `[OrgUnit]` 

`ruleClasses` - `[RuleClass]` 

**Deprecated** Prefer travel policy service for this data 

`travelConfigs` - `[TravelConfig]` 

Arguments 

`filter` - `TravelConfigFilter` 

`companyGroups` - `[CompanyGroup]` 

`t2OptIn` - `T2OptIn` 

**Deprecated** Vendor Groups are no longer in use 

**Deprecated** This is available more accurately through Travel Config 

`partnerServiceVendors` - 

```
[PartnerServiceVendor]
```

## **EXAMPLE** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

191/246 

4/6/26, 2:27 PM 

config-api reference 

```
{
"id": "abc123",
"companyId": 123,
"companyName": "xyz789",
"internetDomain": "xyz789",
"companyDomain": "abc123",
"countryCode": "abc123",
"billingCurrencyCode": "xyz789",
"uuid": "abc123",
"activeSwitch": 987,
"isBillable": true,
"travelOfferingCode": "abc123",
"isUatCompany": true,
"migration": Migration,
"directBillContractReferenceId": "abc123",
"customFields": [CustomField],
"customText": [CustomText],
"domains": [Domain],
"publishedFiles": [PublishedFile],
"locations": [Location],
"modules": [Module],
"orgUnits": [OrgUnit],
"ruleClasses": [RuleClass],
"travelConfigs": [TravelConfig],
"companyGroups": [CompanyGroup],
"t2OptIn": T2OptIn,
"partnerServiceVendors": [PartnerServiceVendor]
}
```

Types 

## **CompanyGroup** 

**DEPRECATED** Vendor Groups 

Field Name Description 

`groupId` - `Int` 

`groupName` - `String` 

`uuid` - `String` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

192/246 

4/6/26, 2:27 PM 

config-api reference 

## **EXAMPLE** 

```
{
"groupId": 987,
"groupName": "xyz789",
"uuid": "abc123"
}
```

## Types 

## **CompanyTuple** 

Field Name 

Description 

`uuid` - `String!` 

`companyName` - `String!` 

## **EXAMPLE** 

```
{
"uuid": "abc123",
"companyName": "abc123"
}
```

Types 

## **ConfigurationItem** 

Field Name 

Description 

`domain` - `String` 

`category` - `String` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

193/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`item` - `String` 

`value` - `String` 

`lastModifiedBy` - `String` 

`lastModifiedUtc` - `String` 

`companyUuid` - `String` 

## **EXAMPLE** 

```
{
"domain": "abc123",
"category": "abc123",
"item": "xyz789",
"value": "xyz789",
"lastModifiedBy": "xyz789",
"lastModifiedUtc": "xyz789",
"companyUuid": "xyz789"
}
```

Types 

## **ConfigurationItemInput** 

Input Field Description 

`configId` - `String!` 

`domain` - `String!` 

`category` - `String! item` - `String!` 

`userId` - `String!` 

`value` - `String` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

194/246 

4/6/26, 2:27 PM 

config-api reference 

Input Field 

Description 

`companyUuid` - `String` 

## **EXAMPLE** 

```
{
"configId": "abc123",
"domain": "xyz789",
"category": "xyz789",
"item": "abc123",
"userId": "xyz789",
"value": "xyz789",
"companyUuid": "xyz789"
}
```

Types 

## **ConfigurationOptions** 

Field Name Description 

`leaveUnusedFQVLNumbers` - `Boolean` 

## **EXAMPLE** 

```
{"leaveUnusedFQVLNumbers": true}
```

Types 

## **ConsortiumHotel** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

195/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`discountCode` - `String` 

`refName` - `String` 

## **EXAMPLE** 

```
{
"discountCode": "xyz789",
"refName": "abc123"
}
```

Types 

## **ContractHotel** 

Field Name Description `chainCode` - `String cdNumber` - `String contractData` - `String propertyId` - `String contractRate` - `BigDecimal hotelRefName` - `String hotelPrefRank` - `Int notes` - `String currencyCode` - `String countryCode` - `String propertyInfo` - `PropertyInfo seasonalRates` - `[ContractHotelSeasonalRates]` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

196/246 

4/6/26, 2:27 PM 

config-api reference 

## **EXAMPLE** 

```
{
"chainCode": "xyz789",
"cdNumber": "abc123",
"contractData": "abc123",
"propertyId": "xyz789",
"contractRate": BigDecimal,
"hotelRefName": "xyz789",
"hotelPrefRank": 123,
"notes": "xyz789",
"currencyCode": "abc123",
"countryCode": "xyz789",
"propertyInfo": PropertyInfo,
"seasonalRates": [ContractHotelSeasonalRates]
}
```

Types 

## **ContractHotelSeasonalRates** 

Field Name Description 

`startDate` - `DateTime` 

`endDate` - `DateTime` 

`contractRate` - `BigDecimal` 

## **EXAMPLE** 

```
{
"startDate": "2007-12-03T10:15:30Z",
"endDate": "2007-12-03T10:15:30Z",
"contractRate": BigDecimal
}
```

Types 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

197/246 

4/6/26, 2:27 PM 

config-api reference 

## **CustomField** 

## Field Name 

`uuid` - `String` 

Description **Deprecated** This returns a v5 uuid which should not be used anymore. Use id field instead 

`id` - `String` 

`attributeId` - `Int!` 

`attributeType` - `String` 

`name` - `String` 

`dataType` - `String` 

`required` - `Boolean` 

`minLength` - `Int` 

`maxLength` - `Int` 

`displayOnItinerary` - `Boolean!` 

`displayTitle` - `String` 

`displayAtStart` - `Boolean!` 

`displayAtEnd` - `Boolean` 

`sort` - `Int` 

`totalValues` - `Int` 

`dependencyFieldId` - `String` 

**Deprecated** This returns a v5 uuid which should not be used anymore. Please contact us if you need a replacement 

`dependencyFieldUuid` - `String` Returns v4 uuid of dependency field 

`dependencyValues` - `[String]` 

`dependencyType` - `String` 

`displayForGuestBooking` - `Boolean` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

198/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`displayForRegularTrips` - `Boolean` 

`displayForTripEdits` - `Boolean` 

`displayForMeetings` - `Boolean!` 

`customFieldValues` - `[CustomFieldValue]` 

Returns field values limited filter, page and size. Page parameter starts with 0. Default is page: 0, size: 1000. Filter is case insensitive on value and text 

Arguments 

`filter` - `String` 

`page` - `Int` 

`size` - `Int` 

`dependsOnField` - `CustomField` 

## **EXAMPLE** 

```
{
"uuid": "xyz789",
"id": "xyz789",
"attributeId": 123,
"attributeType": "abc123",
"name": "xyz789",
"dataType": "xyz789",
"required": true,
"minLength": 987,
"maxLength": 123,
"displayOnItinerary": true,
"displayTitle": "xyz789",
"displayAtStart": true,
"displayAtEnd": false,
"sort": 987,
"totalValues": 123,
"dependencyFieldId": "xyz789",
"dependencyFieldUuid": "xyz789",
"dependencyValues": ["xyz789"],
"dependencyType": "abc123",
"displayForGuestBooking": false,
"displayForRegularTrips": true,
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

199/246 

4/6/26, 2:27 PM 

config-api reference 

```
"displayForTripEdits": true,
"displayForMeetings": true,
"customFieldValues": [CustomFieldValue],
"dependsOnField": CustomField
}
```

Types 

## **CustomFieldValue** 

Field Name Description **Deprecated** This returns a v5 uuid which `id` - `String` should not be used anymore. Please contact us if you need a replacement 

`order` - `Int` 

`value` - `String` 

`text` - `String` 

## **EXAMPLE** 

```
{
"id": "xyz789",
"order": 123,
"value": "xyz789",
"text": "xyz789"
}
```

Types 

## **CustomText** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

200/246 

4/6/26, 2:27 PM 

config-api reference 

|Field Name|Description|
|---|---|
|`fieldName`-`String`|the code name for the custom text (e.g.<br>AirRulesViolation, CarRulesViolation, etc.)|
||the language code associated with the text|
|`languageCode`-`String`|(e.g. en-us) Note: zz-all is used for text that|
||supposed to be used in any language)|
|`value`-`String`|the custom text|
|`useDefault`-`Boolean`|true if the custom text is using the Concur|
||default value and not one provided by the user|



## **EXAMPLE** 

```
{
"fieldName": "abc123",
"languageCode": "abc123",
"value": "abc123",
"useDefault": true
}
```

Types 

## **DateTime** 

## **EXAMPLE** 

```
"2007-12-03T10:15:30Z"
```

Types 

## **DiscountFlags** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

201/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

## From 

`sabreKeepUndiscountedCars` - `Boolean!` 

Scripts/TravelWizard/const_travelWizard.asp: If set, we keep undiscounted car rates that come back when a CD number is sent, otherwise we remove them. Can only be enabled for Car discounts with Sabre GDS type. 

`airPrivateDiscountFaresOnly` - `Boolean!` 

The following 2 discount flags can only be enabled for Air discounts with Apollo, Galileo/Travelport+, or Sabre GDS types. 

`airPrivateAndPublicSeparateSearch` - `Boolean!` 

`amadeusCorporateSeparateSearch` - `Boolean!` 

Can only be enabled for Air discounts with Amadeus GDS type. 

## **EXAMPLE** 

```
{
"sabreKeepUndiscountedCars": false,
"airPrivateDiscountFaresOnly": false,
"airPrivateAndPublicSeparateSearch": false,
"amadeusCorporateSeparateSearch": false
}
```

Types 

## **Domain** 

Field Name Description `name` - `String! companyId` - `Int` 

`isDefault` - `Boolean` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

202/246 

4/6/26, 2:27 PM 

config-api reference 

## **EXAMPLE** 

```
{
"name": "xyz789",
"companyId": 123,
"isDefault": false
}
```

Types 

## **EReceipt** 

Field Name Description 

`enableEreceipts` - `Boolean` 

`allowCliqbookItineraryForAirEreceipt` - `Boolean` 

## **EXAMPLE** 

```
{"enableEreceipts": true, "allowCliqbookItineraryForAirEreceipt": false}
```

Types 

## **EmailOptions** 

Subset of data from OUTTASK_COMPANY_TRAVEL_CONFIG representing email options 

Field Name Description 

`confirmationEmails` - `Int` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

203/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`cancellationEmailSetting` - `Int` 

`holdReminderEmailSubject` - `String` 

Possible values: 

0 = both "Approve Trips Via Email" and "Reject Trips Via Email" options are disabled 

`approvalEmailOptions` - `Int` 

1 = only "Approve Trips Via Email" enabled 

- 2 = only "Reject Trips Via Email" enabled 3 = both options enabled 

## **EXAMPLE** 

```
{
"confirmationEmails": 123,
"cancellationEmailSetting": 123,
"holdReminderEmailSubject": "abc123",
"approvalEmailOptions": 987
}
```

Types 

## **Float** 

The `Float` scalar type represents signed double-precision fractional values as specified by IEEE 754. 

**EXAMPLE** 

```
987.65
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

204/246 

4/6/26, 2:27 PM 

config-api reference 

Types 

## **FormOfPayment** 

Field Name Description 

`creditCardForAirRailRequired` - `Boolean! govOnlyAirfareGhostCardNumber` - `String!` 

if govOnlyAirfareGhostCardType = "##" then `govOnlyAirfareGhostCardType` - `String!` Use agency invoice for government-only airfare is selected 

`govOnlyAirfareGhostCardExpiration` - `DateTime` 

`userCustomPropertyForDefaultCreditCard` - `Int` 

`enforceTempCardBinRestrictions` - `Boolean! tempCardsHotelOnly` - `Boolean! forceCreditCardChoice` - `Boolean!` 

`showPersonalCardsBeforeGhostCards` - `Boolean!` 

## **EXAMPLE** 

```
{
"creditCardForAirRailRequired": false,
"govOnlyAirfareGhostCardNumber": "xyz789",
"govOnlyAirfareGhostCardType": "abc123",
"govOnlyAirfareGhostCardExpiration": "2007-12-03T10:15:30Z",
"userCustomPropertyForDefaultCreditCard": 123,
"enforceTempCardBinRestrictions": true,
"tempCardsHotelOnly": false,
"forceCreditCardChoice": true,
"showPersonalCardsBeforeGhostCards": false
}
```

## Types 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

205/246 

4/6/26, 2:27 PM 

config-api reference 

## **GdsPnr** 

Field Name Description `writeUserSuppliedHotelPassives` - `Boolean requiresGdsPassive` - `Boolean requiresGdsPnr` - `Boolean iWillBookLaterUserSuppliedOption` - `Boolean` 

## **EXAMPLE** 

```
{
"writeUserSuppliedHotelPassives": true,
"requiresGdsPassive": false,
"requiresGdsPnr": true,
"iWillBookLaterUserSuppliedOption": true
}
```

Types 

## **HotelSearch** 

Field Name Description `hotelMaxResults` - `Int preferredPropSearchRadius` - `Int companyLocationsSearchRadius` - `Int defaultHotelSearchRadius` - `Int hotelsWithDepositPermission` - `Boolean hotelDisplaysPerDiemRate` - `Boolean` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

206/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`overrideBookingIataHotel` - `String` Comma Delimited List: PV = Preference Rank, $ = Lowest Price, * = Star Rating, $D = Distance, `hotelSortDefault` - `String` X = Default, A = Company Policy, CUSTOM = custom Hotel Rate Sort Default admin setting: Int `hotelRateSortDefault` - `Int` null/0 = Negotiated Rates (default) 1 = Price, Lowest to Higest 

When hotelSortDefault is CUSTOM, customHotelSortPrimary can be one of these: `customHotelSortPrimary` - `String!` PV = Preference Rank, $ = Lowest Price, * = Star Rating, $D = Distance, A = Company Policy, empty = None When hotelSortDefault is CUSTOM, customHotelSortSecondary can be one of `customHotelSortSecondary` - `String!` these: PV = Preference Rank, $ = Lowest Price, * = Star Rating, $D = Distance, A = Company Policy, , empty = None When hotelSortDefault is CUSTOM, customHotelSortTertiary can be one of these: `customHotelSortTertiary` - `String!` PV = Preference Rank, $ = Lowest Price, * = Star Rating, $D = Distance, A = Company Policy, , empty = None 

## **EXAMPLE** 

```
{
```

- `"hotelMaxResults": 987,` 

- `"preferredPropSearchRadius": 987,` 

- `"companyLocationsSearchRadius": 987,` 

- `"defaultHotelSearchRadius": 123,` 

- `"hotelsWithDepositPermission": true,` 

- `"hotelDisplaysPerDiemRate": true,` 

- `"overrideBookingIataHotel": "xyz789", "hotelSortDefault": "abc123",` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

207/246 

4/6/26, 2:27 PM 

config-api reference 

```
"hotelRateSortDefault": 987,
"customHotelSortPrimary": "xyz789",
"customHotelSortSecondary": "abc123",
"customHotelSortTertiary": "xyz789"
}
```

Types 

## **HotelShop** 

Field Name Description 

`countryCode` - `String` 

`shopGds` - `Boolean` 

`shopHotelService` - `Boolean!` 

`partnerServiceVendor` - `PartnerServiceVendor` 

## **EXAMPLE** 

```
{
"countryCode": "xyz789",
"shopGds": false,
"shopHotelService": false,
"partnerServiceVendor": PartnerServiceVendor
}
```

Types 

## **Int** 

The `Int` scalar type represents non-fractional signed whole numeric values. Int can represent values between -(2^31) and 2^31 - 1. 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

208/246 

4/6/26, 2:27 PM 

config-api reference 

**EXAMPLE** 

```
987
```

Types 

## **Location** 

Field Name Description **Deprecated** This returns a v5 uuid which `id` - `String` should not be used anymore. Please contact us if you need a replacement Returns v4 uuid. Please use this field instead of `uuid` - `String` 'id' (v5 uuid). `companyId` - `Int name` - `String address` - `String city` - `String state` - `String zipCode` - `String countryCode` - `String latitude` - `Float longitude` - `Float` 

`allowDelivery` - `Boolean` 

`vendors` - `[LocationVendor]` 

## **EXAMPLE** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

209/246 

4/6/26, 2:27 PM 

config-api reference 

```
{
"id": "abc123",
"uuid": "xyz789",
"companyId": 987,
"name": "abc123",
"address": "abc123",
"city": "xyz789",
"state": "xyz789",
"zipCode": "abc123",
"countryCode": "abc123",
"latitude": 987.65,
"longitude": 987.65,
"allowDelivery": true,
"vendors": [LocationVendor]
}
```

Types 

## **LocationVendor** 

Field Name Description 

`isVirtual` - `Boolean` 

`chainCode` - `String` 

`stationCode` - `String` 

`effectiveDate` - `DateTime` 

`expiryDate` - `DateTime` 

## **EXAMPLE** 

```
{
"isVirtual": true,
"chainCode": "abc123",
"stationCode": "xyz789",
"effectiveDate": "2007-12-03T10:15:30Z",
"expiryDate": "2007-12-03T10:15:30Z"
}
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

210/246 

4/6/26, 2:27 PM 

config-api reference 

Types 

## **Meeting** 

Field Name Description `outtaskId` - `Int! name` - `String! locationName` - `String! cityCodes` - `[String!]! startDate` - `DateTime! endDate` - `DateTime! matchingStartDate` - `DateTime matchingEndDate` - `DateTime timeZone` - `String!` 

## **EXAMPLE** 

```
{
"outtaskId": 987,
"name": "xyz789",
"locationName": "xyz789",
"cityCodes": ["abc123"],
"startDate": "2007-12-03T10:15:30Z",
"endDate": "2007-12-03T10:15:30Z",
"matchingStartDate": "2007-12-03T10:15:30Z",
"matchingEndDate": "2007-12-03T10:15:30Z",
"timeZone": "abc123"
}
```

## Types 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

211/246 

4/6/26, 2:27 PM 

config-api reference 

## **Migration** 

## **DEPRECATED** Represents migration elements for a company 

Field Name Description `migrationReadyUtc` - `DateTime` 

`migratedElsewhere` - `Boolean` 

## **EXAMPLE** 

```
{
"migrationReadyUtc": "2007-12-03T10:15:30Z",
"migratedElsewhere": false
}
```

## Types 

## **Module** 

Field Name Description 

`companyId` - `Int` 

`moduleCode` - `String!` 

`isActive` - `Boolean!` 

`moduleProperties` - `[ModuleProperty]` 

Arguments `propertyName` - `[String]` 

## **EXAMPLE** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

212/246 

4/6/26, 2:27 PM 

config-api reference 

```
{
"companyId": 987,
"moduleCode": "xyz789",
"isActive": true,
"moduleProperties": [ModuleProperty]
}
```

## Types 

## **ModuleProperty** 

Field Name Description 

`propertyId` - `Int` 

`moduleCode` - `String` 

`propertyName` - `String` 

`propertyValue` - `String` 

`defaultValue` - `String` 

`isCompanyProperty` - `Boolean` 

## **EXAMPLE** 

```
{
"propertyId": 123,
"moduleCode": "abc123",
"propertyName": "abc123",
"propertyValue": "xyz789",
"defaultValue": "xyz789",
"isCompanyProperty": false
}
```

Types 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

213/246 

4/6/26, 2:27 PM 

config-api reference 

## **OrgUnit** 

Field Name Description `orgUnitId` - `Int uuid` - `String orgUnitName` - `String` 

## **EXAMPLE** 

```
{
"orgUnitId": 987,
"uuid": "abc123",
"orgUnitName": "xyz789"
}
```

## Types 

## **PageInfo** 

Field Name Description `hasNextPage` - `Boolean! hasPreviousPage` - `Boolean!` 

## **EXAMPLE** 

```
{"hasNextPage": true, "hasPreviousPage": false}
```

Types 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

214/246 

4/6/26, 2:27 PM 

config-api reference 

## **PartnerServiceVendor** 

Field Name Description 

`baseUrl` - `String` 

`domain` - `String` 

`login` - `String` 

`password` - `String` 

`vendorId` - `Int` 

`vendorCode` - `String` 

`vendorName` - `String` 

`vendorLogo` - `String` 

`microserviceUrl` - `String` 

`apiVersion` - `Int` 

`billingReferenceId` - `String` 

`shortVendorName` - `String` 

`systemRequestorId` - `String` 

`systemRequestorIdType` - `Int!` 

`vendorStatus` - `Boolean` 

## **EXAMPLE** 

```
{
"baseUrl": "abc123",
"domain": "abc123",
"login": "abc123",
"password": "xyz789",
"vendorId": 987,
"vendorCode": "abc123",
"vendorName": "xyz789",
"vendorLogo": "xyz789",
"microserviceUrl": "abc123",
"apiVersion": 987,
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

215/246 

4/6/26, 2:27 PM 

config-api reference 

```
"billingReferenceId": "abc123",
"shortVendorName": "abc123",
"systemRequestorId": "abc123",
"systemRequestorIdType": 987,
```

```
"vendorStatus": true
```

```
}
```

## Types 

## **PnrFinishing** 

Field Name 

Description 

`forceFinishingBeforeApproval` - `Boolean` 

`ticketOption` - `Int` 

`finishingTemplate` - `PublishedFile` 

`addAllBrokenRulesToFinisher` - `Boolean` 

## **EXAMPLE** 

```
{
"forceFinishingBeforeApproval": true,
"ticketOption": 123,
"finishingTemplate": PublishedFile,
"addAllBrokenRulesToFinisher": true
}
```

Types 

## **PolicyOptions** 

Policy options of the travel configuration 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

216/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`ruleClassLabel` - `String` 

`userCanSelectRuleClass` - `Int!` 

`rulesUseBaseFare` - `Boolean` 

`forceRuleClassSelection` - `Boolean` 

`allowMultipleViolationCodes` - `Boolean` 

## **EXAMPLE** 

```
{
"ruleClassLabel": "abc123",
"userCanSelectRuleClass": 987,
"rulesUseBaseFare": false,
"forceRuleClassSelection": true,
"allowMultipleViolationCodes": false
}
```

## Types 

## **ProfileOptions** 

Field Name Description 

`requirePassportInfo` - `Int` 

## **EXAMPLE** 

```
{"requirePassportInfo": 987}
```

Types 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

217/246 

4/6/26, 2:27 PM 

config-api reference 

## **ProfileSyncOptions** 

Field Name Description 

`xmlSyncIdDefault` - `Int gdsProfiles` - `Boolean gdsReadProfiles` - `Boolean syncBeforeSearch` - `Boolean` 

## **EXAMPLE** 

```
{
"xmlSyncIdDefault": 987,
"gdsProfiles": false,
"gdsReadProfiles": true,
"syncBeforeSearch": false
}
```

Types 

## **PropertyInfo** 

Field Name Description 

`latitude` - `Float` 

`longitude` - `Float` 

## **EXAMPLE** 

```
{"latitude": 987.65, "longitude": 123.45}
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

218/246 

4/6/26, 2:27 PM 

config-api reference 

Types 

## **PublishedFile** 

Field Name Description 

`fileId` - `Int companyId` - `Int` 

`purpose` - `Int subtype` - `Int` 

`fileName` - `String` 

`fileExt` - `String` 

`contentType` - `String` 

`publishedFileData` - `[PublishedFileData]` 

Arguments `version` - `Int maxVersion` - `Boolean` 

## **EXAMPLE** 

```
{
"fileId": 987,
"companyId": 987,
"purpose": 123,
"subtype": 987,
"fileName": "abc123",
"fileExt": "xyz789",
"contentType": "xyz789",
"publishedFileData": [PublishedFileData]
}
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

219/246 

4/6/26, 2:27 PM 

config-api reference 

Types 

## **PublishedFileData** 

Field Name Description `fileDataId` - `Int fileId` - `Int updatedAtUtc` - `DateTime updatedBy` - `Int version` - `Int fileData` - `String` 

## **EXAMPLE** 

```
{
"fileDataId": 987,
"fileId": 123,
"updatedAtUtc": "2007-12-03T10:15:30Z",
"updatedBy": 123,
"version": 123,
"fileData": "abc123"
}
```

Types 

## **RailConnector** 

Field Name Description `evolviEnabled` - `Boolean sncfEnabled` - `Boolean` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

220/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`amtrakEnabled` - `Boolean` 

`bibeEnabled` - `Boolean` 

`deutscheBahnEnabled` - `Boolean` 

`generalEnabled` - `Boolean` 

`renfeEnabled` - `Boolean` 

`searchParamsEnabled` - `Boolean` 

`silverRailEnabled` - `Boolean` 

`trainLineEnabled` - `Boolean` 

`viaRailEnabled` - `Boolean` 

## **EXAMPLE** 

```
{
"evolviEnabled": false,
"sncfEnabled": true,
"amtrakEnabled": false,
"bibeEnabled": false,
"deutscheBahnEnabled": false,
"generalEnabled": false,
"renfeEnabled": false,
"searchParamsEnabled": false,
"silverRailEnabled": false,
"trainLineEnabled": true,
"viaRailEnabled": true
}
```

Types 

## **RuleClass** 

## **DEPRECATED** OUTTASK_RULE_CLASS 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

221/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`id` - `String` 

**Deprecated** This returns a v5 uuid which should not be used anymore. Use ruleClassUuid field instead 

`ruleClassId` - `Int` 

`ruleClassUuid` - `String` 

`ruleClassName` - `String` 

`propertyConfigId` - `Int` 

`allowLimo` - `Boolean!` 

`enableUserSuppliedHotels` - `Boolean!` 

`approval` - `Approval` 

`customFields` - `[CustomField]` 

`ruleValues` - `[RuleValue]` 

**Deprecated** Prefer travel policy service for this data 

**Deprecated** Prefer travel policy service for this data 

**Deprecated** Prefer travel policy service for this data 

Arguments 

`ruleGroup` - `String` 

`itineraryRulesCustomFieldCount` - `Int` 

## **EXAMPLE** 

```
{
"id": "xyz789",
"ruleClassId": 123,
"ruleClassUuid": "abc123",
"ruleClassName": "xyz789",
"propertyConfigId": 987,
"allowLimo": true,
"enableUserSuppliedHotels": true,
"approval": Approval,
"customFields": [CustomField],
"ruleValues": [RuleValue],
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

222/246 

4/6/26, 2:27 PM 

config-api reference 

```
"itineraryRulesCustomFieldCount": 987
```

```
}
```

Types 

## **RuleValue** 

## **DEPRECATED** OUTTASK_RULE_VALUES 

Field Name Description 

`ruleValuesXml` - `String` 

`ruleGroup` - `String` 

`violationType` - `String` 

`ruleValueUuid` - `String` 

`andOperator` - `Boolean` 

## **EXAMPLE** 

```
{
"ruleValuesXml": "xyz789",
"ruleGroup": "xyz789",
"violationType": "xyz789",
"ruleValueUuid": "xyz789",
"andOperator": true
}
```

Types 

## **SabreProfile** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

223/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`sabreProfileDomainId` - `String` 

`sabreProfileTemplateId` - `String` 

## **EXAMPLE** 

```
{
"sabreProfileDomainId": "xyz789",
"sabreProfileTemplateId": "xyz789"
}
```

## Types 

## **SharedCustomField** 

Field Name Description `sharingId` - `Int attributeId` - `Int travelConfigId` - `Int` 

`nonGdsBookingSourceCode` - `Int partnerServiceVendorId` - `Int` 

`sharedAttributeId` - `Int companyId` - `Int sharedAttributeName` - `String` 

## **EXAMPLE** 

```
{
"sharingId": 123,
"attributeId": 987,
"travelConfigId": 123,
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

224/246 

4/6/26, 2:27 PM 

config-api reference 

```
"nonGdsBookingSourceCode": 123,
"partnerServiceVendorId": 123,
```

```
"sharedAttributeId": 987,
```

```
"companyId": 987,
"sharedAttributeName": "abc123"
}
```

Types 

## **String** 

The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text. 

## **EXAMPLE** 

```
"xyz789"
```

Types 

## **T2OptIn** 

Field Name Description 

`airOptIn` - `Boolean!` 

`carOptIn` - `Boolean!` 

`hotelOptIn` - `Boolean!` 

`companyAirOptIn` - `Boolean!` 

`companyCarOptIn` - `Boolean!` 

`companyHotelOptIn` - `Boolean!` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

225/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`tmcAirOptIn` - `Boolean!` 

`tmcCarOptIn` - `Boolean!` 

`tmcHotelOptIn` - `Boolean!` 

`uuids` - `[String]` 

This returns true if only TravelSysAdmins can modify the TravelConfig 

`adminOnly` - `Boolean!` 

adminOnly is always false at a Company Level 

## **EXAMPLE** 

```
{
"airOptIn": false,
"carOptIn": true,
"hotelOptIn": false,
"companyAirOptIn": true,
"companyCarOptIn": false,
"companyHotelOptIn": true,
"tmcAirOptIn": true,
"tmcCarOptIn": false,
"tmcHotelOptIn": false,
"uuids": ["xyz789"],
"adminOnly": true
}
```

Types 

## **TravelConfig** 

OUTTASK_COMPANY_TRAVEL_CONFIG - travel configuration 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

226/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`id` - `String` 

`uuid` - `String` 

**Deprecated** This returns a v5 uuid which `t2Id` - `String` should not be used anymore. Use uuid field instead 

`outtaskId` - `String` 

**Deprecated** No longer supported 

`travelConfigName` - `String` 

`bar` - `String` 

`profileTemplateFile` - `PublishedFile` 

`isActive` - `Boolean` 

`castleEnabled` - `Boolean` 

hasParent returns true if `hasParent` - `Boolean` MASTER_TRAVEL_CONFIG_ID is not empty, false otherwise 

`gdsType` - `Int` 

`countryCode` - `String!` 

`accountingCode` - `String!` 

`allowAddAirFfToCarHotel` - `Boolean` 

**Deprecated** This field is now present under type wizardOptions. 

`allowPersonalCreditCardForHotel` - `Boolean` 

`allowTempCardForGuestBooking` - `Boolean` 

`requireCardForCarRental` - `Boolean` 

`agencyInvoiceFopChoice` - `Int` 

`dontWritePassives` - `Boolean` 

`cteTravelRequest` - `Boolean` 

**Deprecated** This field is now present under type wizardOptions. 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

227/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`cteTravelRequestType` - `Int` 

**Deprecated** This field is now present under 

type wizardOptions. 

`defaultPassiveSegments` - `Boolean` 

`itinMessage` - `String` 

`offlineTripPassiveApproval` - `Boolean!` 

`usesLegacyHotelConnector` - `Boolean!` 

`airPlusAidaEnabled` - `Boolean!` 

`travelToolsUrl` - `String!` 

`brandingId` - `Int!` 

`agencyConfig` - `AgencyConfig` 

`company` - `Company` 

`configurationItems` - `[ConfigurationItem]` 

Arguments 

`domain` - `String` 

`category` - `String` 

`item` - `String` 

`configurationItemsHistory` - 

```
[ConfigurationItem]
```

Arguments 

`domain` - `String` 

`category` - `String` 

`item` - `String` 

`consortiumHotels` - `[ConsortiumHotel]` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

228/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

## `contractHotels` - `[ContractHotel]` 

GdsType is Optional, but recommended for best performance; Latitude and Longitude need to be in WGS84 Standard, Radius should be in Kilometers 

Arguments 

`gdsType` - `Int` 

`latitude` - `Float` 

`longitude` - `Float` 

`radius` - `Float` 

`customFields` - `[CustomField]` 

**Deprecated** Prefer custom fields service for this data 

Arguments 

`type` - `String` 

Possible values: 'trip' or 'user' 

`eReceipt` - `EReceipt` 

`emailOptions` - `EmailOptions` 

`formOfPayment` - `FormOfPayment` 

`hotelSearch` - `HotelSearch` 

`pnrFinishing` - `PnrFinishing` 

`profileOptions` - `ProfileOptions` 

`wizardOptions` - `WizardOptions` 

`domains` - `[TravelConfigDomain]` 

Arguments 

`domainCode` - `String` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

229/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`travelConfigItems` - `[TravelConfigItem]` 

Arguments 

`domainCode` - `String` 

`categoryCode` - `String` 

`itemCode` - `String` 

## `tsaSecureFlight` - `TsaSecureFlight` 

`profileSyncOptions` - `ProfileSyncOptions` 

`vendorDiscounts` - `[VendorDiscount]` 

Returns vendor discounts at travel config-level, and company-wide level. 

Arguments 

`travelType` - `String` 

`applyFilter` - `Boolean` 

Default applyFilter = true. If applyFilter is true, company-wide-level discounts will only return if there are no config-level discounts for that particular vendor. 

## `vendorExclusions` - `[VendorExclusion]` 

Arguments 

`travelType` - `String` 

## `violationReasons` - `[ViolationReason]` 

**Deprecated** Prefer travel policy service for this data 

Arguments 

`uuid` - `String` 

`gdsPnr` - `GdsPnr` 

## `bookingSourceOptions` - `[BookingSourceOption]` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

230/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`hotelShop` - `[HotelShop]` 

Arguments 

`countryCode` - `String` 

Returns the Hotel Shop based on the following criteria: 

No countryCode argument is passed: Returns all hotel shop config of this travel config 

countryCode argument passed as null: Returns the global default hotel shop config 

- countryCode argument is not null: Returns the country specific hotel shop config if found, otherwise returns the global default hotel shop config 

## `customText` - `[CustomText]` 

Arguments 

`fieldName` - `[String]` 

`languageCode` - `String` 

`showEmpty` - `Boolean` 

Default: false 

`carSearch` - `CarSearch` 

`sharedCustomFields` - `[SharedCustomField]` 

Arguments 

`nonGdsBookingSourceCode` - `Int` 

`partnerServiceVendorId` - `Int` 

## `tripOptions` - `TripOptions` 

`currencyCode` - `String` 

`policyOptions` - `PolicyOptions` 

`airSearch` - `AirSearch` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

231/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`sabreProfile` - `SabreProfile` 

`airportHubs` - `[AirportHub]` 

`t2OptIn` - `T2OptIn` 

`configOptions` - `ConfigurationOptions` 

`railConnector` - `RailConnector` 

True if Hotel Seasonal Rates with a future end `hasFutureHotelSeasonalRates` - `Boolean` date exist for the company, and either the travel config or the agency's GDS type 

`ruleClass` - `RuleClass` 

This will include all rule classes for the travel `ruleClasses` - `[RuleClass]` config 

`egenciaIntegration` - `Int` 

`contractExternalReferenceId` - `String` 

## **EXAMPLE** 

```
{
"id": "abc123",
"uuid": "xyz789",
"t2Id": "abc123",
"outtaskId": "abc123",
"travelConfigName": "abc123",
"bar": "abc123",
"profileTemplateFile": PublishedFile,
"isActive": false,
"castleEnabled": false,
"hasParent": false,
"gdsType": 987,
"countryCode": "abc123",
"accountingCode": "abc123",
"allowAddAirFfToCarHotel": false,
"allowPersonalCreditCardForHotel": false,
"allowTempCardForGuestBooking": true,
"requireCardForCarRental": true,
"agencyInvoiceFopChoice": 987,
"dontWritePassives": true,
"cteTravelRequest": true,
"cteTravelRequestType": 987,
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

232/246 

4/6/26, 2:27 PM 

config-api reference 

```
"defaultPassiveSegments": false,
"itinMessage": "abc123",
"offlineTripPassiveApproval": false,
"usesLegacyHotelConnector": true,
"airPlusAidaEnabled": false,
"travelToolsUrl": "xyz789",
"brandingId": 987,
"agencyConfig": AgencyConfig,
"company": Company,
"configurationItems": [ConfigurationItem],
"configurationItemsHistory": [ConfigurationItem],
"consortiumHotels": [ConsortiumHotel],
"contractHotels": [ContractHotel],
"customFields": [CustomField],
"eReceipt": EReceipt,
"emailOptions": EmailOptions,
"formOfPayment": FormOfPayment,
"hotelSearch": HotelSearch,
"pnrFinishing": PnrFinishing,
"profileOptions": ProfileOptions,
"wizardOptions": WizardOptions,
"domains": [TravelConfigDomain],
"travelConfigItems": [TravelConfigItem],
"tsaSecureFlight": TsaSecureFlight,
"profileSyncOptions": ProfileSyncOptions,
"vendorDiscounts": [VendorDiscount],
"vendorExclusions": [VendorExclusion],
"violationReasons": [ViolationReason],
"gdsPnr": GdsPnr,
"bookingSourceOptions": [BookingSourceOption],
"hotelShop": [HotelShop],
"customText": [CustomText],
"carSearch": CarSearch,
"sharedCustomFields": [SharedCustomField],
"tripOptions": TripOptions,
"currencyCode": "abc123",
"policyOptions": PolicyOptions,
"airSearch": AirSearch,
"sabreProfile": SabreProfile,
"airportHubs": [AirportHub],
"t2OptIn": T2OptIn,
"configOptions": ConfigurationOptions,
"railConnector": RailConnector,
"hasFutureHotelSeasonalRates": true,
"ruleClass": RuleClass,
"ruleClasses": [RuleClass],
"egenciaIntegration": 123,
"contractExternalReferenceId": "xyz789"
}
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

233/246 

4/6/26, 2:27 PM 

config-api reference 

Types 

## **TravelConfigCategory** 

Field Name Description `domainCode` - `String categoryCode` - `String name` - `String nameMsgId` - `String canBeDisabled` - `Boolean` **Deprecated** This returns a v5 uuid which `travelConfigUuid` - `String` should not be used anymore. Please contact us if you need a replacement `isDisabled` - `Boolean! lastModBy` - `Int` 

`items` - `[TravelConfigItem]` 

Arguments `itemCode` - `String returnDefaultValues` - `Boolean` 

`partnerServiceVendor` - `PartnerServiceVendor` 

`bookingSourceOption` - `BookingSourceOption` 

If this field is null, then this Travel Config Category is not a Booking Source Option. 

## **EXAMPLE** 

```
{
"domainCode": "abc123",
"categoryCode": "abc123",
"name": "abc123",
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

234/246 

4/6/26, 2:27 PM 

config-api reference 

```
"nameMsgId": "xyz789",
"canBeDisabled": true,
"travelConfigUuid": "abc123",
"isDisabled": false,
"lastModBy": 123,
"items": [TravelConfigItem],
"partnerServiceVendor": PartnerServiceVendor,
"bookingSourceOption": BookingSourceOption
}
```

Types 

## **TravelConfigDomain** 

Field Name Description 

`domainCode` - `String` 

`name` - `String` 

`nameMsgId` - `String` 

`categories` - `[TravelConfigCategory]` 

Arguments 

`categoryCode` - `String` 

## **EXAMPLE** 

```
{
"domainCode": "abc123",
"name": "xyz789",
"nameMsgId": "abc123",
"categories": [TravelConfigCategory]
}
```

## Types 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

235/246 

4/6/26, 2:27 PM 

config-api reference 

## **TravelConfigFilter** 

Filter options for querying travel configurations. Supports filtering by active status, country codes, and agency vendor IDs. 

|Input Field|Description|
|---|---|
|`isActive`-`Boolean`|Filter by active/inactive status|
|`castleEnabled`-`Boolean`|Filter by castle enabled status|
|`countryCode`-`[String]`|Filter by one or more country codes (e.g., ["US",<br>"GB", "DE"])|
|`vendorId`-`[Int]`|Filter by agency vendor IDs (requires join with<br>agency table)|



## **EXAMPLE** 

```
{
"isActive": false,
"castleEnabled": true,
"countryCode": ["xyz789"],
"vendorId": [123]
}
```

Types 

## **TravelConfigItem** 

Field Name Description `domainCode` - `String categoryCode` - `String itemCode` - `String` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

236/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`defaultItemValue` - `String` 

`enabled` - `Boolean` 

`mustBeEncrypted` - `Boolean` 

`travelConfigUuid` - `String` 

**Deprecated** This returns a v5 uuid which should not be used anymore. Please contact us if you need a replacement 

`itemValue` - `String` 

`partnerServiceVendor` - `PartnerServiceVendor` 

## **EXAMPLE** 

```
{
"domainCode": "xyz789",
"categoryCode": "xyz789",
"itemCode": "abc123",
"defaultItemValue": "xyz789",
"enabled": false,
"mustBeEncrypted": false,
"travelConfigUuid": "abc123",
"itemValue": "abc123",
"partnerServiceVendor": PartnerServiceVendor
}
```

Types 

## **TravelConfigTuple** 

Field Name Description 

`uuid` - `String!` 

`travelConfigName` - `String!` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

237/246 

4/6/26, 2:27 PM 

config-api reference 

## **EXAMPLE** 

```
{
"uuid": "abc123",
"travelConfigName": "xyz789"
}
```

Types 

## **TripOptions** 

Contains options pertaining to a trip 

Field Name Description 

`allowTripHold` - `Boolean` 

`maxHoldDays` - `Int` 

`maxDaysPassiveApprovalHold` - `Int` 

`autoCancelRejectedTrip` - `Boolean` 

`autoCancelRejectedNonAirTrip` - `Boolean` 

`autoCancelTripHold` - `Boolean` 

`autoCancelApprovalHold` - `Boolean` 

`allowTicketVoid` - `Boolean` 

## **EXAMPLE** 

```
{
"allowTripHold": true,
"maxHoldDays": 123,
"maxDaysPassiveApprovalHold": 123,
"autoCancelRejectedTrip": false,
"autoCancelRejectedNonAirTrip": false,
"autoCancelTripHold": true,
"autoCancelApprovalHold": true,
```

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

238/246 

4/6/26, 2:27 PM 

config-api reference 

```
"allowTicketVoid": false
```

```
}
```

Types 

## **TsaSecureFlight** 

Field Name 

Description 

`enforceSecureFlight` - `Int` 

`sendTsaData` - `Int` 

When to send TSA-required data to air carriers. 0=never, 1=in/out of USA only, 2=always 

`allowBookingWithoutDob` - `Boolean!` 

`writeMiddleNameToPnr` - `Boolean` 

## **EXAMPLE** 

```
{
"enforceSecureFlight": 987,
"sendTsaData": 987,
"allowBookingWithoutDob": true,
"writeMiddleNameToPnr": false
}
```

Types 

## **User** 

Field Name 

Description 

`id` - `String` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

239/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`company` - `Company!` 

`meetings` - `[Meeting]!` 

`companiesAccess` - `[CompanyTuple!]!` 

List of companies that this user has access to, given their roles and divisional view, if enabled. Optional name parameter filters the list of companies by name. Page parameter starts with 0. Default is page: 0, size: 100 

Arguments 

`name` - `String` 

`page` - `Int` 

`size` - `Int` 

`travelConfigsAccess` - `[TravelConfigTuple!]!` 

List of travel configs within the specified company that this user has access to, given their roles and divisional view, if enabled. 

Arguments 

`companyUuid` - `String!` 

## `canAccessCompany` - `Boolean!` 

Arguments 

`uuid` - `String!` 

## `canAccessTravelConfig` - `Boolean!` 

Arguments 

`uuid` - `String!` 

## **EXAMPLE** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

240/246 

4/6/26, 2:27 PM 

config-api reference 

```
{
"id": "abc123",
"company": Company,
"meetings": [Meeting],
"companiesAccess": [CompanyTuple],
"travelConfigsAccess": [TravelConfigTuple],
"canAccessCompany": false,
"canAccessTravelConfig": false
}
```

Types 

## **VendorDiscount** 

## Discounts from _**OUTTASK_TRAVEL_VENDOR_DISCOUNT**_ 

|Field Name|Description|
|---|---|
|`chainCode`-`String`|the travel company code|
|`isPreferred`-`Boolean`|true if vendor is preferred|
|`extraData`-`String`|'CD Number' is stored here|
|`prefRank`-`Int`|preference rank|
|`discountCode`-`String`|the discount code|
|`travelCompanyType`-`String`|the travel company type (i.e. A, C, H)|
|`airDiscountType`-`String`|discount type used for air|
|`isCorporateRateOnlySearch`-`Boolean`|only used for car discounts|
||Returns "orgunit", "travelconfig", "company" or|
|`discountLevel`-`String`|"other". This field is useful for debugging|
||purposes.|
|`payAsYouFlyCode`-`String`||



https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

241/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Field Name Description Where the Billing Reference Number (BR) is `promoCode` - `String!` stored `airMoreFaresBics` - `String` Where the Billing Number (BN) is stored `isRail` - `Boolean!` true if it is a Rail vendor 

`discountFlags` - `DiscountFlags` 

## **EXAMPLE** 

```
{
"chainCode": "xyz789",
"isPreferred": false,
"extraData": "xyz789",
"prefRank": 987,
"discountCode": "abc123",
"travelCompanyType": "abc123",
"airDiscountType": "xyz789",
"isCorporateRateOnlySearch": false,
"discountLevel": "xyz789",
"payAsYouFlyCode": "abc123",
"promoCode": "xyz789",
"airMoreFaresBics": "abc123",
"isRail": false,
"discountFlags": DiscountFlags
}
```

Types 

## **VendorExclusion** 

Field Name 

Description 

`chainCode` - `String` 

## **EXAMPLE** 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

242/246 

4/6/26, 2:27 PM 

config-api reference 

```
{"chainCode": "abc123"}
```

Types 

## **ViolationReason** 

**DEPRECATED** - OUTTASK_TRAVEL_VIOLATION_REASONS 

Field Name Description 

`id` - `String` 

`companyReasonCode` - `String` 

`violationType` - `String` 

`description` - `String` 

`isActive` - `Boolean` 

`violationReasonCodeUUID` - `String` 

## **EXAMPLE** 

```
{
"id": "abc123",
"companyReasonCode": "xyz789",
"violationType": "abc123",
"description": "abc123",
"isActive": false,
"violationReasonCodeUUID": "abc123"
}
```

Types 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

243/246 

4/6/26, 2:27 PM 

config-api reference 

## **WizardOptions** 

Field Name 

Description 

`showGovHotel` - `Int` 

`allowAddAirFfToCarHotel` - `Boolean` 

`cteTravelRequest` - `Boolean!` 

`cteTravelRequestType` - `Int` 

`cteBookingSwitch` - `Boolean!` 

`allowAddAirToExistingItin` - `Boolean` 

`serviceClassDefaultLowest` - `Boolean` 

`llfWindowSource` - `Int!` 

`captureLlfFlifo` - `Boolean` 

Show additional LLF screen when: 

- 0 = User's chosen fare is out of policy 

`llfScreenShowWhen` - `Int` 

- 1 = User's chosen fare is more expensive 2 = Any cheaper options exist within LLF's time window 

The LLF screen display the user's chosen fare and: 

- 0 = The LLF option(s) 

`llfScreenShowFlights` - `Int` 

- 1 = All in-policy fares within the time window 

- 2 = All cheaper, in-policy fares within the time window 

`enableChurnDetection` - `Int` 

`churnAirlines` - `String` 

`enableDuplicateDetection` - `Boolean` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

244/246 

4/6/26, 2:27 PM 

config-api reference 

Field Name 

Description 

`dupDetectionAirlines` - `String` 

`showMorningAfternoonEveningOptions` - `Boolean` 

`limitFarelistLlfWindow` - `Boolean!` 

`showCommentsToAgentBox` - `Boolean!` 

`showAgentCommentsWarning` - `Boolean!` 

`maxCompanions` - `Int!` 

`defaultDepartureHour` - `Int` Default value is 9:00 am 

`defaultReturnHour` - `Int` Default value is 3:00 pm 

`mixedCarriersSplitMode` - `Int!` 

`segmentFeesEnabled` - `Boolean` 

- 0 = From Schedule Search, using discounts and ticketing arrangements 1 = From Schedule and Price Search, when split is cheaper 2 = From Schedule Search, price without splitting and use no discounts 

`fastTrackEnabled` - `Boolean` 

## **EXAMPLE** 

```
{
"showGovHotel": 987,
"allowAddAirFfToCarHotel": true,
```

```
"cteTravelRequest": true,
```

- `"cteTravelRequestType": 987,` 

```
"cteBookingSwitch": false,
```

- `"allowAddAirToExistingItin": true,` 

```
"serviceClassDefaultLowest": false,
"llfWindowSource": 123,
"captureLlfFlifo": true,
"llfScreenShowWhen": 987,
"llfScreenShowFlights": 987,
"enableChurnDetection": 123,
"churnAirlines": "xyz789",
"enableDuplicateDetection": true,
```

- `"dupDetectionAirlines": "xyz789",` 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

245/246 

4/6/26, 2:27 PM 

config-api reference `"showMorningAfternoonEveningOptions": true, "limitFarelistLlfWindow": true, "showCommentsToAgentBox": true, "showAgentCommentsWarning": true, "maxCompanions": 123, "defaultDepartureHour": 987, "defaultReturnHour": 123, "mixedCarriersSplitMode": 987, "segmentFeesEnabled": true, "fastTrackEnabled": true }` 

Documentation by Anvil SpectaQL 

https://pages.github.concur.com/travel-admin/config-api/schema/index.html#query-travelConfigs 

246/246 

