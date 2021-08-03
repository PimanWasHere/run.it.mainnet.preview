pragma solidity ^0.4.23;

contract Ownable {
  address public owner;


    event OwnershipRenounced(address indexed previousOwner);
    event OwnershipTransferred(
    address indexed previousOwner,
    address indexed newOwner
  );


  /**
   * @dev The Ownable constructor sets the original `owner` of the contract to the sender
   * account.
   */
  constructor() public {
    owner = msg.sender;
  }

  /**
   * @dev Throws if called by any account other than the owner.
   */
  modifier onlyOwner() {
    require(msg.sender == owner);
    _;
  }

  // As below - A Soul cannot transfer their profile nor renounceOwnership (but they can delete the contract)


  /**
   * @dev Allows the current owner to transfer control of the contract to a newOwner.
   * @param newOwner The address to transfer ownership to.

  function transferOwnership(address newOwner) public onlyOwner {
    require(newOwner != address(0));
    emit OwnershipTransferred(owner, newOwner);
    owner = newOwner;
  }
  */

  /**
   * @dev Allows the current owner to relinquish control of the contract.

  function renounceOwnership() public onlyOwner {
    emit OwnershipRenounced(owner);
    owner = address(0);
  }
  */

}







contract runitprofile is Ownable {
  using SafeMath for uint256;

// owner set via ownable constructor to deployer
// Run.it has 'Souls' not 'Users'.. they own their own data.


string private fname;
string private lname;
string private nickname;
string private phone;
string private nationality;
string private rolecode;
// rolecode permitted values P/F/S/C/B/R/D   R=sponsor - for duplicate and ease of install.
address private runitaccountid; // this is the Run.it accountid that holds HBARs and holds RUN tokens in the ERC20
uint256 private runitbal;  // updated from Run token SC when inquiry refresh _isApprovedOrOwner
string private hederafileid;    // this is the Run.it accountid in Users terms (holds account/keys,pwrdhash,profile scc addr)
string private dataipfshash;
address private platformaddress;





// demo, behavioral, interests
// can be kept on a tiny cost hedera file or pinned to IPFS for PoC / pre-production
// hedera files, like SCs are on Hedera to ABFT math defined level of security. - the highest known.

// mapping(address => uint256) hedera interests file; // for use later for PoC .. maybe keep interest keywords on a hedera file - cheaper in GAS

// Likes and interests - PoC small interest selection for demo purposes. 'categories to choose from or indexes'.

string private interest1;
string private interest2;
string private interest3;

// the following are public so platform can see the openness OR not of the Owner, as permissions for the platform and Sponsors to
// see the data owners decisions ie so Data owner canb get RUN token rewards
// - but only Contract OnlyOwner can update.

bool public demographic;
bool public behavioral;
bool public interests;

uint256 public sponsorslevel;
uint256 public grpsponsorslevel;
bool public kycapproved;           //  set true or false - after 3rd praty plugin/ or in App KYC - driv lic pic or other TBD


// Sponsor exposure measure 0 - 10 0= none, 3 low, 5 medium, 10 high  to maximize rewards.





  constructor(string _fname, string _lname, string _nickname, string _phone, string _nationality, string _rolecode, address _aacountid, uint256 _initialrunbal, string _hederafileid, string _dataipfshash, address _platformaddress) public {

// Run.it account is a hedera public key/assigned Account assigned at time of onboarding.
// impersonation is IMPOSSIBLE if friends aware of the public key and Run.it account# for this Soul

    platformaddress = _platformaddress;

    fname = _fname;
    lname = _lname;
    nickname = _nickname;
    phone = _phone;
    nationality = _nationality;
    rolecode = _rolecode;
    runitaccountid = _aacountid;
    runitbal = _initialrunbal;
    hederafileid = _hederafileid;
    dataipfshash = _dataipfshash;

    kycapproved = false;


  }


// Events broadcast to ledger as public but anonymous receipt, if needs be.


 event Profilecreated(
    address smartcontractid
    );

 event Profileupdated(
   address runitaccountid
    );

  event Interestsupdated(
    address runitaccountid
     );

  event Opennessupdated(
   address runitaccountid
    );


// custom Modifier for Owner OR Platform - Run.it

  modifier onlyOwnerorrunit() {
    require((msg.sender == platformaddress) || (msg.sender == owner));
    _;
  }



    // getters for Owner only!

  function getfname() view onlyOwner public returns(string) {

    return fname;
  }


  function getlname() view onlyOwner public returns(string) {

    return lname;
  }

  function getnickname() view onlyOwner public returns(string) {

    return nickname;
  }


  function getphone() view onlyOwner public returns(string) {

    return phone;
  }


  function getnationality() view onlyOwner public returns(string) {

    return nationality;
  }

// only platform and Owner can see the roles - needed by DApp to custom the dashboard



function getrolecode() view onlyOwnerorrunit public returns(string) {

  return rolecode;
}

function getrunaccountid() view onlyOwnerorrunit public returns(address) {

  return runitaccountid;
}

// in case Soul forgets their Runit account id. ie the hedera fileid.
function gethederafileid() view onlyOwnerorrunit public returns(string) {

  return hederafileid;
}

function getdataipfshash() view onlyOwner public returns(string) {

  return dataipfshash;
}






// only owner can view AND update these

  function getinterest1() view onlyOwner public returns(string) {

    return interest1;
  }


  function getinterest2() view onlyOwner public returns(string) {

    return interest2;
  }


  function getinterest3() view onlyOwner public returns(string) {

    return interest3;
  }

// Run.it OR orfile Owner can see these - for matching purposes IF they have profile openness permission - TBD on degree of/ granularity
// this will a re-write for an array of interest.. more interests more gas it will cost user to maintain - micro cents!
// this will also apply to profile getter methods for MvP later on .. for demo and  behaviorial

    function runitgetinterest1() view onlyOwnerorrunit public returns(string) {

      return interest1;
    }


    function runitgetinterest2() view onlyOwnerorrunit public returns(string) {

      return interest2;
    }


    function runitgetinterest3() view onlyOwnerorrunit public returns(string) {

      return interest3;
    }






 // update profile by Soul ONLY ie OnlyOwner.

  function updateprofile (string _fname, string _lname, string _nickname, string _phone, string _nationality, string _rolecode)  public  onlyOwner{

    fname = _fname;
    lname = _lname;
    nickname = _nickname;
    phone = _phone;
    nationality = _nationality;
    rolecode = _rolecode;

  }

 // used to update the profile because the profile SC contractID is stored in the Run.it fileID(ieaccount) But
 // the profile also is to hold the run.it account (hedera fileid).. chick & egg. So this method below is called after the File create in the DApp

  function updaterunitaccountid(string _createdrunitfileid) public onlyOwner {

  hederafileid = _createdrunitfileid;

  }



    function updateinterests(string _interest1, string _interest2, string _interest3, bool _demo, bool _behav, bool _inter, uint256 _sponsorslevel, uint256 _grpsponsorslevel) public onlyOwner{


      interest1 = _interest1;
      interest2 = _interest2;
      interest3 = _interest3;

      demographic = _demo;
      behavioral = _behav;
      interests = _inter;

      sponsorslevel = _sponsorslevel;
      grpsponsorslevel = _grpsponsorslevel;

    }



  function removeprofile() public onlyOwner{

    // selfdestruct profile smart contract by the Run.it Soul only.

    selfdestruct(this);

 }



}



library SafeMath {

  /**
  * @dev Multiplies two numbers, throws on overflow.
  */
  function mul(uint256 a, uint256 b) internal pure returns (uint256) {
    if (a == 0) {
      return 0;
    }
    uint256 c = a * b;
    assert(c / a == b);
    return c;
  }

  /**
  * @dev Integer division of two numbers, truncating the quotient.
  */
  function div(uint256 a, uint256 b) internal pure returns (uint256) {
    // assert(b > 0); // Solidity automatically throws when dividing by 0
    uint256 c = a / b;
    // assert(a == b * c + a % b); // There is no case in which this doesn't hold
    return c;
  }

  /**
  * @dev Subtracts two numbers, throws on overflow (i.e. if subtrahend is greater than minuend).
  */
  function sub(uint256 a, uint256 b) internal pure returns (uint256) {
    assert(b <= a);
    return a - b;
  }

  /**
  * @dev Adds two numbers, throws on overflow.
  */
  function add(uint256 a, uint256 b) internal pure returns (uint256) {
    uint256 c = a + b;
    assert(c >= a);
    return c;
  }
}
