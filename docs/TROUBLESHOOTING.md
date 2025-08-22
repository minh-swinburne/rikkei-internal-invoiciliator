# Invoice Reconciliator - Troubleshooting Guide

## Network and API Connection Issues

### Known Issue: API Connection Failures with Valid Keys

**Status**: Under Investigation  
**Reported**: August 22, 2025  
**Reporter**: US-based tester  

#### Symptoms
- User enters valid OpenRouter API key
- Application fails to connect during processing
- Error occurs even though user can access openrouter.ai website directly
- Different error than typical "invalid API key" messages

#### Potential Causes
1. **Corporate Network Restrictions**
   - Firewall blocking specific API endpoints
   - Proxy servers interfering with HTTPS requests
   - DPI (Deep Packet Inspection) blocking AI service requests
   - VPN routing issues

2. **SSL/TLS Certificate Issues**
   - Corporate certificates not trusted by Python requests
   - SSL handshake failures
   - Certificate chain validation problems

3. **HTTP/HTTPS Protocol Restrictions**
   - Corporate policies blocking POST requests to AI services
   - Content filtering based on request patterns
   - Rate limiting at network level

4. **Regional/Geographic Restrictions**
   - Different API endpoints for different regions
   - CDN routing issues
   - ISP-level blocking of AI services

#### Diagnostic Steps for Users
1. **Test Connection Method**
   ```
   Settings → LLM Configuration → Test Connection
   ```
   - Note the exact error message
   - Try multiple times to check for intermittent issues

2. **Network Environment Check**
   - Are you on a corporate network?
   - Are you using a VPN?
   - Can you test from a different network (mobile hotspot)?

3. **Browser vs App Comparison**
   - Can you access https://openrouter.ai/api/v1/chat/completions in browser?
   - Does the website work but API calls fail?

4. **Firewall/Antivirus Check**
   - Temporarily disable corporate firewall
   - Add application to antivirus exceptions
   - Check if Python executable is blocked

#### Temporary Workarounds
1. **Network Change**
   - Try from personal network/mobile hotspot
   - Use different VPN endpoint
   - Contact IT for API endpoint allowlisting

2. **Alternative Models**
   - Try different OpenRouter models
   - Test with different base URLs if available

#### Technical Investigation Needed
- [ ] Add more detailed network error logging
- [ ] Implement connection diagnostics tool
- [ ] Add proxy support configuration
- [ ] Include SSL certificate verification options
- [ ] Add timeout and retry configuration

#### Related Error Patterns
- `ConnectionError`: Network-level blocking
- `SSLError`: Certificate validation issues  
- `TimeoutError`: Network latency/blocking
- `ProxyError`: Corporate proxy interference

---

## Other Common Issues

### Application Won't Start
**Cause**: Missing dependencies or corrupted installation
**Solution**: 
1. Reinstall from fresh download
2. Check Python environment if running from source
3. Verify all required files are present

### PDF Processing Fails
**Cause**: Corrupted or image-only PDF files
**Solution**:
1. Ensure PDFs contain readable text (not just scanned images)
2. Verify PDF files contain both invoice and purchase order
3. Check file size (very large files may timeout)

### Settings Not Saving
**Cause**: File permissions or corrupted settings
**Solution**:
1. Run as administrator (Windows)
2. Check write permissions to application directory
3. Delete settings file to reset: `%APPDATA%\KDDI\Invoice Reconciliator`

### Performance Issues
**Cause**: System resources or network latency
**Solution**:
1. Close other applications to free memory
2. Check internet connection speed
3. Adjust timeout settings in configuration

---

## Reporting Issues

When reporting issues, please include:

1. **System Information**
   - Operating System and version
   - Network environment (corporate/home/VPN)
   - Antivirus/firewall software

2. **Error Details**
   - Exact error messages
   - Steps to reproduce
   - Application logs (Help → Copy Logs)

3. **Network Environment**
   - Corporate vs home network
   - VPN usage
   - Proxy configuration
   - Firewall settings

4. **API Testing Results**
   - Test Connection results
   - Alternative network testing
   - Browser access verification

---

## Version History

### v1.0 (August 2025)
- Initial release
- Known issue: Network connectivity problems in corporate environments

---

*This document will be updated as we gather more information about network-related issues.*
